<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Core\Exceptions\NotFound;
use Espo\Modules\CommercialIntelligence\Services\VisibilityInheritanceService;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * GET-only evidence-review surface for hidden governed source records.
 *
 * The entity and field registries are intentionally closed. This action
 * cannot expose arbitrary Espo entities or fields and has no mutation path.
 */
final class GetGovernedSourceDetail implements Action
{
    private const MIN_ENTITY_ID_LENGTH = 8;
    private const MAX_ENTITY_ID_LENGTH = 36;

    /** @var array<string, list<string>> */
    private const ENTITY_FIELDS = [
        'AIJob' => [
            'name',
            'capability',
            'purpose',
            'status',
            'attemptCount',
            'failureCategory',
            'nextRetryAt',
            'startedAt',
            'completedAt',
            'resultReference',
            'createdAt',
        ],
        'AIRequestLog' => [
            'name',
            'capability',
            'purpose',
            'attemptNumber',
            'status',
            'failureCategory',
            'latencyMs',
            'costAmount',
            'costCurrency',
            'createdAt',
        ],
        'ResearchEvidence' => [
            'name',
            'peEvidenceId',
            'peClaim',
            'peClaimType',
            'evidenceType',
            'classificationReason',
            'validationState',
            'peSourceUrl',
            'peContentSummary',
            'peConfidence',
            'peCapturedAt',
            'peSchemaVersion',
            'peSnapshotHash',
            'peCanonicalUrl',
            'provenanceReference',
            'evidenceRevision',
            'createdAt',
            'modifiedAt',
        ],
        'AIQualificationInsight' => [
            'name',
            'insightContent',
            'signals',
            'reasoning',
            'confidence',
            'evidenceReferences',
            'createdAt',
        ],
        'HumanFeedback' => [
            'name',
            'feedbackType',
            'comment',
            'assessment',
            'actor',
            'createdAt',
        ],
        'ProspectCandidate' => [
            'name',
            'candidateKey',
            'externalReference',
            'createdAt',
        ],
        'ProspectRun' => [
            'name',
            'runKey',
            'executionScope',
            'maxCandidates',
            'status',
            'createdAt',
        ],
        'ExecutionLedger' => [
            'name',
            'eventType',
            'outcome',
            'failureCategory',
            'actor',
            'occurredAt',
            'createdAt',
        ],
        'ReplyEvent' => [
            'name',
            'externalEventId',
            'replyStatus',
            'receivedAt',
            'sendTraceReference',
            'triageStatus',
            'closedReason',
            'closedAt',
            'createdAt',
            'modifiedAt',
        ],
        'OptimizationInsight' => [
            'name',
            'insightType',
            'title',
            'description',
            'recommendation',
            'evidenceReference',
            'sourcePeriodStart',
            'sourcePeriodEnd',
            'generatedAt',
            'freshnessStatus',
            'confidence',
            'status',
            'reviewedAt',
            'decisionNote',
            'createdAt',
        ],
        'PerformanceMetric' => [
            'name',
            'metricType',
            'metricValue',
            'aggregationPeriod',
            'sampleSize',
            'confidenceLevel',
            'freshnessStatus',
            'sourceReference',
            'generatedAt',
            'createdAt',
        ],
        'FeedbackLearningObservation' => [
            'name',
            'observationType',
            'description',
            'sourceReference',
            'feedbackReference',
            'metricReference',
            'aggregationPeriodStart',
            'aggregationPeriodEnd',
            'confidence',
            'sampleSize',
            'freshnessStatus',
            'status',
            'createdAt',
        ],
        'ReplySignal' => [
            'name',
            'sourceReference',
            'interpretation',
            'confidence',
            'provenance',
            'freshnessStatus',
            'status',
            'transitionedAt',
            'transitionedByReference',
            'decisionNote',
            'createdAt',
        ],
        'OpportunityCandidate' => [
            'name',
            'provenanceReference',
            'status',
            'reviewContext',
            'commercialSignalSummary',
            'lastTransitionBy',
            'lastTransitionAt',
            'outcomeReference',
            'outcomeNote',
            'outcomeRecordedAt',
            'createdAt',
        ],
        'RevenueInsight' => [
            'name',
            'sourceReference',
            'provenance',
            'insightSummary',
            'interpretation',
            'confidence',
            'metricReferences',
            'reportingPeriod',
            'freshnessStatus',
            'reviewStatus',
            'reviewNote',
            'createdAt',
        ],
        'PipelineMetric' => [
            'metricName',
            'metricType',
            'value',
            'unit',
            'reportingPeriod',
            'methodology',
            'provenance',
            'freshnessStatus',
            'createdAt',
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private VisibilityInheritanceService $visibility,
    ) {}

    public function process(Request $request): Response
    {
        // The workspace gate runs first so direct URLs cannot disclose whether
        // a governed type or record exists to an unauthorized or portal user.
        $this->visibility->assertWorkspaceAccess();

        $entityType = trim((string) $request->getRouteParam('entityType'));
        $entityId = trim((string) $request->getRouteParam('entityId'));

        if (!$this->isAllowedRequest($entityType, $entityId)) {
            throw new NotFound();
        }

        $entity = $this->entityManager->getEntity($entityType, $entityId);

        if ($entity === null || !$this->visibility->canReadSource($entity)) {
            throw new NotFound();
        }

        return ResponseComposer::json([
            'designation' => 'Read-only governed source',
            'truthBoundary' => 'Source evidence from its owning layer; not assembled CRM truth.',
            'entityType' => $entityType,
            'entityId' => $entityId,
            'displayName' => $this->displayName($entity),
            'fields' => $this->presentFields($entityType, $entity),
        ]);
    }

    private function isAllowedRequest(string $entityType, string $entityId): bool
    {
        if (!isset(self::ENTITY_FIELDS[$entityType])) {
            return false;
        }

        $length = strlen($entityId);

        return $length >= self::MIN_ENTITY_ID_LENGTH
            && $length <= self::MAX_ENTITY_ID_LENGTH
            && preg_match('/\A[A-Za-z0-9]+\z/D', $entityId) === 1;
    }

    private function displayName(Entity $entity): ?string
    {
        foreach (['name', 'title', 'metricName'] as $field) {
            $value = $entity->get($field);
            if (is_string($value) && trim($value) !== '') {
                return trim($value);
            }
        }

        return null;
    }

    /** @return list<array{name: string, label: string, value: string|int|float}> */
    private function presentFields(string $entityType, Entity $entity): array
    {
        $result = [];

        foreach (self::ENTITY_FIELDS[$entityType] as $field) {
            $value = $entity->get($field);

            if (is_bool($value)) {
                $value = $value ? 'Yes' : 'No';
            }
            if (!is_string($value) && !is_int($value) && !is_float($value)) {
                continue;
            }
            if (is_string($value) && trim($value) === '') {
                continue;
            }

            $result[] = [
                'name' => $field,
                'label' => $this->fieldLabel($field),
                'value' => $value,
            ];
        }

        return $result;
    }

    private function fieldLabel(string $field): string
    {
        $label = preg_replace('/(?<!^)([A-Z])/', ' $1', $field);

        return ucfirst($label ?? $field);
    }
}
