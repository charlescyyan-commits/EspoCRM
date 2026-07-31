<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C20 provenance adapter (ADR-C25-005 §3.1).
 *
 * Permitted: read-only reference to AIJob and AIRequestLog records as
 * provenance and cost context for displayed evidence.
 *
 * Forbidden: any AI runtime, routing, or boundary role — C20 owns all of
 * those exclusively. WP1 performs no AI invocation of any kind. No write
 * path exists in this class.
 */
final class C20ProvenanceReadAdapter
{
    public const ENTITY_TYPES = [
        'AIJob',
        'AIRequestLog',
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
