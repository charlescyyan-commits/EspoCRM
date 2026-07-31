<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Exceptions\NotFound;
use Espo\Modules\CommercialIntelligence\Context\ArtifactReferenceParser;
use Espo\Modules\CommercialIntelligence\Context\CommercialContext;
use Espo\Modules\CommercialIntelligence\Services\Adapters\C20ProvenanceReadAdapter;
use Espo\Modules\CommercialIntelligence\Services\Adapters\C21IntelligenceReadAdapter;
use Espo\Modules\CommercialIntelligence\Services\Adapters\C22ExecutionReadAdapter;
use Espo\Modules\CommercialIntelligence\Services\Adapters\C23OptimizationReadAdapter;
use Espo\Modules\CommercialIntelligence\Services\Adapters\C24RevenueReadAdapter;
use Espo\Modules\CommercialIntelligence\Services\Adapters\CrmCoreAnchorReadAdapter;
use Espo\ORM\Entity;

/**
 * Runtime CommercialContext assembly (ADR-C25-001 §3).
 *
 * Trigger boundary: HUMAN REQUEST ONLY. This service runs exclusively in
 * the request cycle of an explicit human action. No background,
 * scheduled, or event-driven invocation of any kind is permitted
 * (ADR-C25-001 §6; charter §8).
 *
 * Boundary rules: no mutation, no lifecycle control, no authority
 * transfer, no reinterpretation of source artifacts.
 */
final class ContextAssemblyService
{
    /** Human-request-only trigger marker (ADR-C25-001 §6). */
    public const TRIGGER = 'HUMAN_REQUEST_ONLY';

    /** Maximum reference-following depth from the anchor. */
    private const MAX_DEPTH = 2;

    /** Governed reference fields scanned for cross-artifact links. */
    private const REFERENCE_FIELDS = [
        'provenanceReference',
        'sourceReference',
        'reviewContext',
        'transitionHistory',
        'lifecycleAudit',
        'metricReferences',
        'evidenceReference',
        'provenance',
    ];

    public function __construct(
        private C24RevenueReadAdapter $c24Revenue,
        private C21IntelligenceReadAdapter $c21Intelligence,
        private C22ExecutionReadAdapter $c22Execution,
        private C23OptimizationReadAdapter $c23Optimization,
        private CrmCoreAnchorReadAdapter $crmCoreAnchor,
        private C20ProvenanceReadAdapter $c20Provenance,
        private VisibilityInheritanceService $visibility,
        private ProvenancePresenter $provenancePresenter,
        private FreshnessPresenter $freshnessPresenter,
    ) {}

    /**
     * Assemble a CommercialContext for an OpportunityCandidate anchor.
     * The result is rendered and discarded — never persisted.
     */
    public function assembleForCandidate(string $candidateId): CommercialContext
    {
        $anchor = $this->c24Revenue->read('OpportunityCandidate', $candidateId);
        if ($anchor === null || !$this->visibility->canReadSource($anchor)) {
            // Visibility inheritance: no anchor access, no workspace view.
            throw new NotFound(
                'OpportunityCandidate anchor not found for commercial context assembly.'
            );
        }

        $context = new CommercialContext();
        $context->setAnchor('OpportunityCandidate', $anchor->getId(), $anchor->get('name'));
        $this->attach($context, 'c24', $anchor, 'C24');

        $visited = ['OpportunityCandidate:' . $anchor->getId() => true];
        $this->assembleReferences($context, $anchor, 0, $visited);

        return $context;
    }

    /**
     * Follow governed text references from a source artifact and attach
     * every readable artifact to its layer section.
     *
     * @param array<string, bool> $visited
     */
    private function assembleReferences(
        CommercialContext $context,
        Entity $source,
        int $depth,
        array &$visited
    ): void {
        if ($depth >= self::MAX_DEPTH) {
            return;
        }

        $references = ArtifactReferenceParser::parse(
            ...$this->referenceValues($source)
        );

        foreach ($references as $reference) {
            $key = $reference['entityType'] . ':' . $reference['entityId'];
            if (isset($visited[$key])) {
                continue;
            }
            $visited[$key] = true;

            [$layer, $entity] = $this->resolve(
                $reference['entityType'],
                $reference['entityId']
            );
            if ($layer === null || $entity === null) {
                continue;
            }
            if (!$this->visibility->canReadSource($entity)) {
                // Source-permission check: not visible at the source layer
                // → not displayed by C25 (visibility inheritance).
                continue;
            }

            $this->attach($context, $this->sectionFor($layer), $entity, $layer);
            $this->assembleReferences($context, $entity, $depth + 1, $visited);
        }
    }

    /**
     * Route an entity type to its owning layer's read-only adapter.
     *
     * @return array{?string, ?Entity}
     */
    private function resolve(string $entityType, string $entityId): array
    {
        if (in_array($entityType, C24RevenueReadAdapter::ENTITY_TYPES, true)) {
            return ['C24', $this->c24Revenue->read($entityType, $entityId)];
        }
        if (in_array($entityType, C21IntelligenceReadAdapter::ENTITY_TYPES, true)) {
            return ['C21', $this->c21Intelligence->read($entityType, $entityId)];
        }
        if (in_array($entityType, C22ExecutionReadAdapter::ENTITY_TYPES, true)) {
            return ['C22', $this->c22Execution->read($entityType, $entityId)];
        }
        if (in_array($entityType, C23OptimizationReadAdapter::ENTITY_TYPES, true)) {
            return ['C23', $this->c23Optimization->read($entityType, $entityId)];
        }
        if (in_array($entityType, CrmCoreAnchorReadAdapter::ENTITY_TYPES, true)) {
            return ['CRM Core', $this->crmCoreAnchor->read($entityType, $entityId)];
        }
        if (in_array($entityType, C20ProvenanceReadAdapter::ENTITY_TYPES, true)) {
            return ['C20', $this->c20Provenance->read($entityType, $entityId)];
        }

        return [null, null];
    }

    private function attach(
        CommercialContext $context,
        string $section,
        Entity $entity,
        string $layer
    ): void {
        $reference = $this->provenancePresenter->present($entity, $layer);

        $context->addArtifact(
            $section,
            $reference,
            $this->freshnessPresenter->present($reference)
        );
    }

    private function sectionFor(string $layer): string
    {
        return match ($layer) {
            'C24' => 'c24',
            'C21' => 'c21',
            'C22' => 'c22',
            'C23' => 'c23',
            'CRM Core' => 'crmCore',
            'C20' => 'c20',
            default => 'other',
        };
    }

    /** @return list<string> */
    private function referenceValues(Entity $entity): array
    {
        $values = [];

        foreach (self::REFERENCE_FIELDS as $field) {
            if (!$entity->hasAttribute($field)) {
                continue;
            }
            $value = $entity->get($field);
            if (is_string($value) && $value !== '') {
                $values[] = $value;
                continue;
            }
            if (is_array($value)) {
                foreach ($value as $item) {
                    if (is_string($item) && $item !== '') {
                        $values[] = $item;
                    }
                }
            }
        }

        return $values;
    }
}
