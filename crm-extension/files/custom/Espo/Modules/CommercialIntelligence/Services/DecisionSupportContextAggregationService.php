<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Aggregates named WP2.2 / WP3 / C24 references into DecisionSupportContext.
 *
 * Commercial Decision Support Layer = human-facing advisory intelligence interface.
 * Does not mutate C24, C22, or CRM Core entities.
 * Does not invoke C24 transitions.
 */
final class DecisionSupportContextAggregationService
{
    public const ENTITY_TYPE = 'DecisionSupportContext';
    public const STATUS_OPEN = 'OPEN';
    public const STATUS_CLOSED = 'CLOSED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private Wp4ReadOnlySourceService $readOnlySources,
        private DecisionSupportProvenanceValidator $provenanceValidator,
    ) {
    }

    /**
     * @param array{
     *   name: string,
     *   commercialBriefIds?: list<string>,
     *   commercialInsightIds?: list<string>,
     *   businessReviewContextIds?: list<string>,
     *   opportunityCandidateId?: string,
     *   revenueInsightId?: string,
     *   pipelineMetricId?: string,
     *   sourceEvidenceReference: string,
     *   capabilityReference?: string,
     *   purposeReference?: string
     * } $input
     */
    public function assemble(array $input): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden('DecisionSupportContext create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        if ($name === '') {
            throw new BadRequest('DecisionSupportContext name is required.');
        }

        $capability = trim((string) (
            $input['capabilityReference']
                ?? DecisionSupportProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? DecisionSupportProvenanceValidator::PURPOSE_COMMERCIAL_DECISION_SUPPORT
        ));
        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        /** @var list<string> $briefIds */
        $briefIds = $this->stringList($input['commercialBriefIds'] ?? null);
        /** @var list<string> $insightIds */
        $insightIds = $this->stringList($input['commercialInsightIds'] ?? null);
        /** @var list<string> $reviewContextIds */
        $reviewContextIds = $this->stringList($input['businessReviewContextIds'] ?? null);

        if ($briefIds === []) {
            throw new BadRequest(
                'DecisionSupportContext requires at least one CommercialBrief reference.'
            );
        }

        $candidateId = trim((string) ($input['opportunityCandidateId'] ?? ''));
        $revenueId = trim((string) ($input['revenueInsightId'] ?? ''));
        $pipelineId = trim((string) ($input['pipelineMetricId'] ?? ''));

        $snapshot = [
            'briefs' => [],
            'insights' => [],
            'businessReviewContexts' => [],
            'opportunityCandidate' => null,
            'revenueInsight' => null,
            'pipelineMetric' => null,
            'assistantRole' => 'human-facing-advisory-intelligence-interface',
            'workspaceRole' => 'commercial-decision-support-layer',
            'mutation' => 'none',
            'transitionInvocation' => 'none',
        ];

        foreach ($briefIds as $briefId) {
            $snapshot['briefs'][] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_COMMERCIAL_BRIEF,
                $briefId
            );
        }
        foreach ($insightIds as $insightId) {
            $snapshot['insights'][] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_COMMERCIAL_INSIGHT,
                $insightId
            );
        }
        foreach ($reviewContextIds as $contextId) {
            $snapshot['businessReviewContexts'][] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_BUSINESS_REVIEW_CONTEXT,
                $contextId
            );
        }
        if ($candidateId !== '') {
            $snapshot['opportunityCandidate'] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_OPPORTUNITY_CANDIDATE,
                $candidateId
            );
        }
        if ($revenueId !== '') {
            $snapshot['revenueInsight'] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_REVENUE_INSIGHT,
                $revenueId
            );
        }
        if ($pipelineId !== '') {
            $snapshot['pipelineMetric'] = $this->readOnlySources->readReference(
                Wp4ReadOnlySourceService::ENTITY_PIPELINE_METRIC,
                $pipelineId
            );
        }

        /** @var Entity $context */
        $context = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $context->set([
            'name' => $name,
            'status' => self::STATUS_OPEN,
            'commercialBriefReferences' => json_encode(
                $briefIds,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'commercialInsightReferences' => json_encode(
                $insightIds,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'businessReviewContextReferences' => json_encode(
                $reviewContextIds,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'opportunityCandidateReference' => $candidateId !== '' ? $candidateId : null,
            'revenueInsightReference' => $revenueId !== '' ? $revenueId : null,
            'pipelineMetricReference' => $pipelineId !== '' ? $pipelineId : null,
            'aggregationSnapshot' => json_encode(
                $snapshot,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        $this->entityManager->saveEntity($context, [
            Wp4DecisionSupportSaveOption::CONTEXT_CREATE_AUTHORIZED => true,
        ]);

        return $context;
    }

    public function close(string $id, string $reason): Entity
    {
        $this->assertHumanCloser();

        $id = trim($id);
        $context = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$context || $context->isNew()) {
            throw new BadRequest('DecisionSupportContext does not exist.');
        }
        if (!$this->acl->checkEntityRead($context)) {
            throw new Forbidden();
        }
        if ((string) $context->get('status') !== self::STATUS_OPEN) {
            throw new Conflict('DecisionSupportContext must be OPEN before CLOSE.');
        }
        if (trim($reason) === '') {
            throw new BadRequest('DecisionSupportContext close requires a reason.');
        }

        $context->set([
            'status' => self::STATUS_CLOSED,
            'closedBy' => trim((string) $this->user->getId()),
            'closedAt' => (new DateTimeImmutable())->format('Y-m-d H:i:s'),
        ]);

        $this->entityManager->saveEntity($context, [
            Wp4DecisionSupportSaveOption::CONTEXT_CLOSE_AUTHORIZED => true,
        ]);

        return $context;
    }

    private function assertHumanCloser(): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                'DecisionSupportContext close requires a human; AI/system cannot decide or approve.'
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden(
                'DecisionSupportContext close requires an authenticated human actor.'
            );
        }
    }

    /**
     * @return list<string>
     */
    private function stringList(mixed $value): array
    {
        if (!is_array($value)) {
            return [];
        }

        return array_values(array_filter(array_map(
            static fn ($v): string => trim((string) $v),
            $value
        )));
    }
}
