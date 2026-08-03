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
 * Aggregates read-only WP2.2 / C24 references into a BusinessReviewContext.
 *
 * Does not mutate C24, C22, or CRM Core entities.
 */
final class BusinessReviewContextAggregationService
{
    public const ENTITY_TYPE = 'BusinessReviewContext';
    public const STATUS_OPEN = 'OPEN';
    public const STATUS_CLOSED = 'CLOSED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private Wp3ReadOnlySourceService $readOnlySources,
        private InsightProvenanceValidator $provenanceValidator,
    ) {
    }

    /**
     * @param array{
     *   name: string,
     *   commercialBriefIds?: list<string>,
     *   commercialInsightIds?: list<string>,
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
            throw new Forbidden('BusinessReviewContext create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        if ($name === '') {
            throw new BadRequest('BusinessReviewContext name is required.');
        }

        $capability = trim((string) (
            $input['capabilityReference']
                ?? InsightProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? InsightProvenanceValidator::PURPOSE_COMMERCIAL_INSIGHT_ADVISORY
        ));
        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        /** @var list<string> $briefIds */
        $briefIds = array_values(array_filter(array_map(
            static fn ($v): string => trim((string) $v),
            is_array($input['commercialBriefIds'] ?? null) ? $input['commercialBriefIds'] : []
        )));
        /** @var list<string> $insightIds */
        $insightIds = array_values(array_filter(array_map(
            static fn ($v): string => trim((string) $v),
            is_array($input['commercialInsightIds'] ?? null) ? $input['commercialInsightIds'] : []
        )));

        $candidateId = trim((string) ($input['opportunityCandidateId'] ?? ''));
        $revenueId = trim((string) ($input['revenueInsightId'] ?? ''));
        $pipelineId = trim((string) ($input['pipelineMetricId'] ?? ''));

        $snapshot = [
            'briefs' => [],
            'insights' => [],
            'opportunityCandidate' => null,
            'revenueInsight' => null,
            'pipelineMetric' => null,
            'assistantRole' => 'human-facing-advisory-intelligence-interface',
            'mutation' => 'none',
        ];

        foreach ($briefIds as $briefId) {
            $snapshot['briefs'][] = $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_COMMERCIAL_BRIEF,
                $briefId
            );
        }
        foreach ($insightIds as $insightId) {
            $entity = $this->entityManager->getEntity('CommercialInsight', $insightId);
            $snapshot['insights'][] = [
                'entityType' => 'CommercialInsight',
                'id' => $insightId,
                'exists' => $entity && !$entity->isNew(),
                'name' => $entity && !$entity->isNew() ? (string) $entity->get('name') : null,
            ];
        }
        if ($candidateId !== '') {
            $snapshot['opportunityCandidate'] = $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_OPPORTUNITY_CANDIDATE,
                $candidateId
            );
        }
        if ($revenueId !== '') {
            $snapshot['revenueInsight'] = $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_REVENUE_INSIGHT,
                $revenueId
            );
        }
        if ($pipelineId !== '') {
            $snapshot['pipelineMetric'] = $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_PIPELINE_METRIC,
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
            'opportunityCandidateReference' => $candidateId !== '' ? $candidateId : null,
            'revenueInsightReference' => $revenueId !== '' ? $revenueId : null,
            'pipelineMetricReference' => $pipelineId !== '' ? $pipelineId : null,
            'aggregationSnapshot' => json_encode(
                $snapshot,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        $this->entityManager->saveEntity($context, [
            Wp3InsightSaveOption::REVIEW_CONTEXT_CREATE_AUTHORIZED => true,
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
            throw new BadRequest('BusinessReviewContext does not exist.');
        }
        if (!$this->acl->checkEntityRead($context)) {
            throw new Forbidden();
        }
        if ((string) $context->get('status') !== self::STATUS_OPEN) {
            throw new Conflict('BusinessReviewContext must be OPEN before CLOSE.');
        }
        if (trim($reason) === '') {
            throw new BadRequest('BusinessReviewContext close requires a reason.');
        }

        $actor = trim((string) $this->user->getId());
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s');
        $context->set([
            'status' => self::STATUS_CLOSED,
            'closedBy' => $actor,
            'closedAt' => $timestamp,
        ]);

        $this->entityManager->saveEntity($context, [
            Wp3InsightSaveOption::REVIEW_CONTEXT_CLOSE_AUTHORIZED => true,
        ]);

        return $context;
    }

    private function assertHumanCloser(): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                'BusinessReviewContext close requires a human; AI/system cannot decide or approve.'
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden('BusinessReviewContext close requires an authenticated human actor.');
        }
    }
}
