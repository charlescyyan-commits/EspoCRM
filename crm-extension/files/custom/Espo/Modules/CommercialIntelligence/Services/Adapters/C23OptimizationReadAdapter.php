<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C23 adapter (ADR-C25-005 §3.4).
 *
 * Permitted: read-only consumption of OptimizationInsight and
 * PerformanceMetric as prospecting effectiveness context.
 *
 * Forbidden: redefining, overwriting, or creating a competing version of
 * C23 optimization metrics; generating optimization recommendations. No
 * write path exists in this class.
 */
final class C23OptimizationReadAdapter
{
    public const ENTITY_TYPES = [
        'OptimizationInsight',
        'PerformanceMetric',
        'FeedbackLearningObservation',
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
