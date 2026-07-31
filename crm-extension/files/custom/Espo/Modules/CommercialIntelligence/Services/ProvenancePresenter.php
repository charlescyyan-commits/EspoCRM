<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Modules\CommercialIntelligence\Context\SourceArtifactReference;
use Espo\ORM\Entity;

/**
 * Builds provenance display references for governed source artifacts
 * (ADR-C25-005 §4). Every displayed artifact preserves:
 *
 *   - source artifact identity (entity type + ID)
 *   - source revision (at assembly time)
 *   - freshness information (passed through unchanged)
 *   - validation state (the source's own governance state, unchanged)
 *   - evidence reference (one-click source navigation target)
 *
 * C25 MUST NOT rewrite evidence meaning: values are carried through
 * unchanged — no reinterpretation, no reclassification, no recomputation,
 * and no paraphrase that alters advisory or factual content.
 */
final class ProvenancePresenter
{
    private const GOVERNED_SOURCE_TYPES = [
        'AIJob',
        'AIRequestLog',
        'ResearchEvidence',
        'AIQualificationInsight',
        'HumanFeedback',
        'ProspectCandidate',
        'ProspectRun',
        'ExecutionLedger',
        'ReplyEvent',
        'OptimizationInsight',
        'PerformanceMetric',
        'FeedbackLearningObservation',
        'ReplySignal',
        'OpportunityCandidate',
        'RevenueInsight',
        'PipelineMetric',
    ];

    private const CRM_CORE_TYPES = [
        'Account',
        'Contact',
        'Opportunity',
    ];

    public function present(Entity $entity, string $layer): SourceArtifactReference
    {
        $entityType = $entity->getEntityType();

        return new SourceArtifactReference(
            entityType: $entityType,
            entityId: $entity->getId(),
            layer: $layer,
            revision: $this->revisionOf($entity),
            freshnessStatus: $this->stringOrNull($entity->get('freshnessStatus')),
            validationState: $this->validationStateOf($entity),
            evidenceReference: $this->evidenceReference($entityType, $entity->getId()),
            displayName: $this->stringOrNull($entity->get('name')),
        );
    }

    private function revisionOf(Entity $entity): ?string
    {
        foreach (['evidenceRevision', 'modifiedAt', 'createdAt'] as $field) {
            $value = $this->stringOrNull($entity->get($field));
            if ($value !== null) {
                return $value;
            }
        }

        return null;
    }

    private function validationStateOf(Entity $entity): ?string
    {
        foreach (['validationState', 'status', 'reviewStatus'] as $field) {
            $value = $this->stringOrNull($entity->get($field));
            if ($value !== null) {
                return $value;
            }
        }

        return null;
    }

    private function evidenceReference(string $entityType, string $entityId): string
    {
        if (in_array($entityType, self::GOVERNED_SOURCE_TYPES, true)) {
            return '#CommercialIntelligenceWorkspace/source/entityType='
                . rawurlencode($entityType)
                . '&entityId='
                . rawurlencode($entityId);
        }

        if (in_array($entityType, self::CRM_CORE_TYPES, true)) {
            return '#' . $entityType . '/view/' . rawurlencode($entityId);
        }

        // A non-navigable value is safer than a broken or arbitrary route.
        return '';
    }

    private function stringOrNull(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
