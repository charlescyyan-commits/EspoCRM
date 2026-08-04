<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\EntityManager;

/**
 * Read-only consumption gate for WP4 Decision Support sources.
 *
 * Never saves or mutates CommercialBrief / CommercialInsight /
 * BusinessReviewContext / C24 / C22 / CRM Core entities.
 */
final class Wp4ReadOnlySourceService
{
    public const ENTITY_COMMERCIAL_BRIEF = 'CommercialBrief';
    public const ENTITY_COMMERCIAL_INSIGHT = 'CommercialInsight';
    public const ENTITY_BUSINESS_REVIEW_CONTEXT = 'BusinessReviewContext';
    public const ENTITY_OPPORTUNITY_CANDIDATE = 'OpportunityCandidate';
    public const ENTITY_REVENUE_INSIGHT = 'RevenueInsight';
    public const ENTITY_PIPELINE_METRIC = 'PipelineMetric';

    /** @var list<string> */
    private const READ_ONLY_TYPES = [
        self::ENTITY_COMMERCIAL_BRIEF,
        self::ENTITY_COMMERCIAL_INSIGHT,
        self::ENTITY_BUSINESS_REVIEW_CONTEXT,
        self::ENTITY_OPPORTUNITY_CANDIDATE,
        self::ENTITY_REVENUE_INSIGHT,
        self::ENTITY_PIPELINE_METRIC,
    ];

    /** @var list<string> */
    private const FORBIDDEN_MUTATION_TYPES = [
        'ProspectRun',
        'ExecutionLedger',
        'ActionGate',
        'Outreach',
        'Lead',
        'Opportunity',
        'Account',
        'Contact',
        self::ENTITY_OPPORTUNITY_CANDIDATE,
        self::ENTITY_REVENUE_INSIGHT,
        self::ENTITY_PIPELINE_METRIC,
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
                "WP4 may only read-reference allowed intelligence sources; {$entityType} is not allowed."
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

    public function assertNotMutationTarget(string $entityType): void
    {
        $entityType = trim($entityType);
        if (in_array($entityType, self::FORBIDDEN_MUTATION_TYPES, true)) {
            throw new Forbidden("WP4 must not mutate {$entityType}.");
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
