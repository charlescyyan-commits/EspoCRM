<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C22 adapter (ADR-C25-005 §3.3).
 *
 * Permitted: read-only consumption of execution outcomes (ProspectCandidate,
 * ProspectRun, ExecutionLedger, ReplyEvent) as execution history for
 * commercial provenance tracing.
 *
 * Forbidden: starting or altering any run, mutating any ledger, triggering
 * outreach, or granting execution permission. C25 data never reaches any
 * execution authorization point. No write path exists in this class.
 */
final class C22ExecutionReadAdapter
{
    public const ENTITY_TYPES = [
        'ProspectCandidate',
        'ProspectRun',
        'ExecutionLedger',
        'ReplyEvent',
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
