<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\EntityManager;

/**
 * Read-only consumption gate for WP2.2 / C24 sources.
 *
 * Never saves or mutates CommercialBrief / C24 / C22 / CRM Core entities.
 */
final class Wp3ReadOnlySourceService
{
    public const ENTITY_COMMERCIAL_BRIEF = 'CommercialBrief';
    public const ENTITY_OPPORTUNITY_CANDIDATE = 'OpportunityCandidate';
    public const ENTITY_REVENUE_INSIGHT = 'RevenueInsight';
    public const ENTITY_PIPELINE_METRIC = 'PipelineMetric';

    /** @var list<string> */
    private const READ_ONLY_TYPES = [
        self::ENTITY_COMMERCIAL_BRIEF,
        self::ENTITY_OPPORTUNITY_CANDIDATE,
        self::ENTITY_REVENUE_INSIGHT,
        self::ENTITY_PIPELINE_METRIC,
    ];

    /** @var list<string> */
    private const FORBIDDEN_MUTATION_TYPES = [
        'ProspectRun',
        'ExecutionLedger',
        'ActionGate',
        'Lead',
        'Opportunity',
        'Account',
        'Contact',
    ];

    public function __construct(
        private EntityManager $entityManager,
    ) {
    }

    /**
     * @return array{entityType: string, id: string, name: ?string, exists: bool}
     */
    public function readReference(string $entityType, string $id): array
    {
        $entityType = trim($entityType);
        $id = trim($id);
        if ($id === '') {
            return [
                'entityType' => $entityType,
                'id' => '',
                'name' => null,
                'exists' => false,
            ];
        }
        if (!in_array($entityType, self::READ_ONLY_TYPES, true)) {
            throw new Forbidden(
                "WP3 may only read-reference allowed intelligence sources; {$entityType} is not allowed."
            );
        }
        if (in_array($entityType, self::FORBIDDEN_MUTATION_TYPES, true)) {
            throw new Forbidden(
                "WP3 must not touch {$entityType} ownership or lifecycle."
            );
        }

        $entity = $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            return [
                'entityType' => $entityType,
                'id' => $id,
                'name' => null,
                'exists' => false,
            ];
        }

        return [
            'entityType' => $entityType,
            'id' => (string) $entity->getId(),
            'name' => $entity->get('name') !== null ? (string) $entity->get('name') : null,
            'exists' => true,
        ];
    }

    /**
     * Hard fail if caller attempts a forbidden mutation type.
     */
    public function assertNotMutationTarget(string $entityType): void
    {
        $entityType = trim($entityType);
        if (
            in_array($entityType, self::FORBIDDEN_MUTATION_TYPES, true)
            || in_array($entityType, self::READ_ONLY_TYPES, true)
        ) {
            // READ_ONLY_TYPES may be read but never mutated by WP3 services.
            if (in_array($entityType, self::FORBIDDEN_MUTATION_TYPES, true)) {
                throw new Forbidden(
                    "WP3 must not mutate {$entityType}."
                );
            }
        }
    }

    /**
     * @return list<string>
     */
    public function readOnlyEntityTypes(): array
    {
        return self::READ_ONLY_TYPES;
    }
}
