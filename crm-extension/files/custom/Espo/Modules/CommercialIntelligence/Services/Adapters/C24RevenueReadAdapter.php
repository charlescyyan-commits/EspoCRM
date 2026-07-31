<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C24 adapter (ADR-C25-005 §3.5).
 *
 * Permitted: read-only consumption of ReplySignal, OpportunityCandidate,
 * RevenueInsight, and PipelineMetric as evidence for commercial
 * intelligence assembly.
 *
 * Forbidden: any mutation — no status change, field update, transition
 * execution, or lifecycle mutation. No write path exists in this class.
 */
final class C24RevenueReadAdapter
{
    public const ENTITY_TYPES = [
        'ReplySignal',
        'OpportunityCandidate',
        'RevenueInsight',
        'PipelineMetric',
    ];

    public function __construct(private EntityManager $entityManager) {}

    public function read(string $entityType, string $entityId): ?Entity
    {
        if (!in_array($entityType, self::ENTITY_TYPES, true)) {
            return null;
        }

        return $this->entityManager->getEntity($entityType, $entityId);
    }
}
