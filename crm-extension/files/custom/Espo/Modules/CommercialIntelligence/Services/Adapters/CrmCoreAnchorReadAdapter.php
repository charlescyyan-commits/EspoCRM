<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services\Adapters;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only CRM Core anchor adapter (ADR-C25-005 §3.6).
 *
 * Permitted: read-only consumption of Account, Contact, and Opportunity
 * records as commercial context anchors.
 *
 * Forbidden: create, modify, close, reopen, stage-transition, or
 * forecast-commit on any CRM Core entity; no `createEntity`/`saveEntity`
 * or lifecycle method call exists in this class; no C25 artifact holds a
 * foreign-key reference to any CRM Core entity.
 */
final class CrmCoreAnchorReadAdapter
{
    public const ENTITY_TYPES = [
        'Account',
        'Contact',
        'Opportunity',
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
