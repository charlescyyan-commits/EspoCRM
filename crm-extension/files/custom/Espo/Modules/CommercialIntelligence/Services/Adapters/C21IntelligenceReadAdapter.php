<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C21 adapter (ADR-C25-005 §3.2).
 *
 * Permitted: read-only consumption of ResearchEvidence,
 * AIQualificationInsight, and HumanFeedback as intelligence context.
 *
 * Forbidden: create, modify, delete, reinterpret, or create a parallel
 * authority for C21 intelligence; no scoring, ranking, or qualification
 * capability exists in this class.
 */
final class C21IntelligenceReadAdapter
{
    public const ENTITY_TYPES = [
        'ResearchEvidence',
        'AIQualificationInsight',
        'HumanFeedback',
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
