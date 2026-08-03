<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates CommercialInsight advisory proposals (fixture / stub / deterministic only).
 *
 * Revenue Analyst Assistant = human-facing advisory intelligence interface.
 * No live provider invocation.
 */
final class CommercialInsightProposalService
{
    public const ENTITY_TYPE = 'CommercialInsight';
    public const STATUS_GENERATED = 'GENERATED';

    public const SOURCE_FIXTURE = 'FIXTURE';
    public const SOURCE_STUB = 'STUB';
    public const SOURCE_DETERMINISTIC = 'DETERMINISTIC';

    /** @var list<string> */
    private const ALLOWED_SOURCES = [
        self::SOURCE_FIXTURE,
        self::SOURCE_STUB,
        self::SOURCE_DETERMINISTIC,
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private InsightProvenanceValidator $provenanceValidator,
        private Wp3ReadOnlySourceService $readOnlySources,
    ) {
    }

    /**
     * @param array{
     *   name: string,
     *   advisoryContent: string,
     *   advisorySource: string,
     *   sourceEvidenceReference: string,
     *   commercialBriefReference?: string,
     *   opportunityCandidateReference?: string,
     *   revenueInsightReference?: string,
     *   pipelineMetricReference?: string,
     *   capabilityReference?: string,
     *   purposeReference?: string
     * } $input
     */
    public function createProposal(array $input): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden('CommercialInsight proposal create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        $content = trim((string) ($input['advisoryContent'] ?? ''));
        $source = trim((string) ($input['advisorySource'] ?? ''));
        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $capability = trim((string) (
            $input['capabilityReference']
                ?? InsightProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? InsightProvenanceValidator::PURPOSE_COMMERCIAL_INSIGHT_ADVISORY
        ));

        if ($name === '' || $content === '') {
            throw new BadRequest('CommercialInsight name and advisoryContent are required.');
        }
        if (!in_array($source, self::ALLOWED_SOURCES, true)) {
            throw new BadRequest(
                'CommercialInsight advisorySource must be FIXTURE, STUB, or DETERMINISTIC.'
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        $briefRef = trim((string) ($input['commercialBriefReference'] ?? ''));
        $candidateRef = trim((string) ($input['opportunityCandidateReference'] ?? ''));
        $revenueRef = trim((string) ($input['revenueInsightReference'] ?? ''));
        $pipelineRef = trim((string) ($input['pipelineMetricReference'] ?? ''));

        if ($briefRef !== '') {
            $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_COMMERCIAL_BRIEF,
                $briefRef
            );
        }
        if ($candidateRef !== '') {
            $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_OPPORTUNITY_CANDIDATE,
                $candidateRef
            );
        }
        if ($revenueRef !== '') {
            $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_REVENUE_INSIGHT,
                $revenueRef
            );
        }
        if ($pipelineRef !== '') {
            $this->readOnlySources->readReference(
                Wp3ReadOnlySourceService::ENTITY_PIPELINE_METRIC,
                $pipelineRef
            );
        }

        /** @var Entity $insight */
        $insight = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $insight->set([
            'name' => $name,
            'reviewStatus' => self::STATUS_GENERATED,
            'advisoryContent' => $content,
            'advisorySource' => $source,
            'sourceEvidenceReference' => $evidence,
            'commercialBriefReference' => $briefRef !== '' ? $briefRef : null,
            'opportunityCandidateReference' => $candidateRef !== '' ? $candidateRef : null,
            'revenueInsightReference' => $revenueRef !== '' ? $revenueRef : null,
            'pipelineMetricReference' => $pipelineRef !== '' ? $pipelineRef : null,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
            'transitionHistory' => '[]',
        ]);

        $this->entityManager->saveEntity($insight, [
            Wp3InsightSaveOption::INSIGHT_CREATE_AUTHORIZED => true,
        ]);

        return $insight;
    }
}
