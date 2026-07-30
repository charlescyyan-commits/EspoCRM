<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates and reads immutable, advisory-only aggregate recommendations.
 *
 * This boundary accepts aggregate evidence references as data. It never
 * resolves or mutates source records, executes a recommendation, or changes
 * CRM workflow state.
 */
final class OptimizationInsightService
{
    public const ENTITY_TYPE = 'OptimizationInsight';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'insightType',
        'title',
        'description',
        'recommendation',
        'evidenceReference',
        'sourcePeriodStart',
        'sourcePeriodEnd',
        'generatedAt',
        'freshnessStatus',
        'confidence',
        'status',
        'supersedesInsightId',
    ];

    /** @var list<string> */
    private const FRESHNESS_STATUSES = [
        'CURRENT',
        'AGING',
        'STALE',
        'ARCHIVAL',
    ];

    /** @var list<string> */
    private const SOURCE_ENTITY_TYPES = [
        'ProspectRun',
        'ExecutionLedger',
        'ActionGate',
        'IntelligenceAggregate',
        'AIJob',
        'AIRequestLog',
        'PerformanceMetric',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {
    }

    /**
     * @param array<string, mixed> $attributes
     */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }

        $attributes = $this->validate($attributes);
        $insight = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $insight->set([
            'name' => 'Optimization Insight: ' . $attributes['title'],
            ...$attributes,
        ]);

        $this->entityManager->saveEntity($insight, [
            C23AnalyticsSaveOption::OPTIMIZATION_INSIGHT_CREATE_AUTHORIZED => true,
        ]);

        return $insight;
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $insight = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$insight || $insight->isNew()) {
            throw new BadRequest('OptimizationInsight does not exist.');
        }
        if (!$this->acl->checkEntityRead($insight)) {
            throw new Forbidden();
        }

        return $insight;
    }

    /**
     * @param array<string, mixed> $attributes
     * @return array<string, mixed>
     */
    public function validate(array $attributes): array
    {
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest(
                'OptimizationInsight contains unsupported fields.'
            );
        }

        $start = $this->requiredDate($attributes, 'sourcePeriodStart');
        $end = $this->requiredDate($attributes, 'sourcePeriodEnd');
        if ($start > $end) {
            throw new BadRequest(
                'OptimizationInsight source period must be chronological.'
            );
        }

        $supersedesInsightId = $this->optionalId(
            $attributes['supersedesInsightId'] ?? null
        );
        if ($supersedesInsightId !== null) {
            $this->assertSupersession($supersedesInsightId);
        }

        return [
            'insightType' => $this->requiredText($attributes, 'insightType'),
            'title' => $this->requiredText($attributes, 'title'),
            'description' => $this->requiredText($attributes, 'description'),
            'recommendation' => $this->requiredText(
                $attributes,
                'recommendation'
            ),
            'evidenceReference' => json_encode(
                $this->aggregateReferences(
                    $attributes['evidenceReference'] ?? null,
                    'evidenceReference'
                ),
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'sourcePeriodStart' => $start->format('Y-m-d H:i:s'),
            'sourcePeriodEnd' => $end->format('Y-m-d H:i:s'),
            'generatedAt' => $this->requiredDate(
                $attributes,
                'generatedAt'
            )->format('Y-m-d H:i:s'),
            'freshnessStatus' => $this->freshnessStatus(
                $attributes['freshnessStatus'] ?? null
            ),
            'confidence' => $this->confidence(
                $attributes['confidence'] ?? null
            ),
            'status' => $this->initialStatus($attributes['status'] ?? null),
            'supersedesInsightId' => $supersedesInsightId,
        ];
    }

    /**
     * @return list<array{entityType: string, reference: string}>
     */
    private function aggregateReferences(mixed $value, string $field): array
    {
        if (!is_array($value) || $value === [] || count($value) > 100) {
            throw new BadRequest(
                "OptimizationInsight {$field} requires 1 to 100 references."
            );
        }

        $references = [];
        foreach ($value as $reference) {
            if (!is_array($reference)) {
                throw new BadRequest(
                    "OptimizationInsight {$field} must contain reference objects."
                );
            }
            $entityType = $reference['entityType'] ?? null;
            $aggregateKey = $reference['reference'] ?? null;
            if (
                !is_string($entityType)
                || !in_array($entityType, self::SOURCE_ENTITY_TYPES, true)
                || !is_string($aggregateKey)
                || trim($aggregateKey) === ''
            ) {
                throw new BadRequest(
                    "OptimizationInsight {$field} contains an invalid aggregate reference."
                );
            }
            $references[] = [
                'entityType' => $entityType,
                'reference' => trim($aggregateKey),
            ];
        }

        return $references;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredText(array $attributes, string $field): string
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("OptimizationInsight requires {$field}.");
        }

        return trim($value);
    }

    /** @param array<string, mixed> $attributes */
    private function requiredDate(array $attributes, string $field): DateTimeImmutable
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("OptimizationInsight requires {$field}.");
        }
        try {
            return new DateTimeImmutable($value);
        } catch (\Exception) {
            throw new BadRequest("OptimizationInsight {$field} must be a date.");
        }
    }

    private function freshnessStatus(mixed $value): string
    {
        if (!is_string($value) || !in_array($value, self::FRESHNESS_STATUSES, true)) {
            throw new BadRequest('OptimizationInsight has an invalid freshnessStatus.');
        }

        return $value;
    }

    private function confidence(mixed $value): float
    {
        if (
            (!is_int($value) && !is_float($value))
            || $value < 0
            || $value > 1
        ) {
            throw new BadRequest(
                'OptimizationInsight confidence must be between 0 and 1.'
            );
        }

        return (float) $value;
    }

    private function initialStatus(mixed $value): string
    {
        if ($value !== null && $value !== 'GENERATED') {
            throw new BadRequest(
                'OptimizationInsight new records must be GENERATED.'
            );
        }

        return 'GENERATED';
    }

    private function assertSupersession(string $predecessorId): void
    {
        $predecessor = $this->entityManager->getEntity(
            self::ENTITY_TYPE,
            $predecessorId
        );
        if (!$predecessor || $predecessor->isNew()) {
            throw new BadRequest(
                'OptimizationInsight supersession requires an existing predecessor.'
            );
        }
        if (!$this->acl->checkEntityRead($predecessor)) {
            throw new Forbidden();
        }

        $successor = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['supersedesInsightId' => $predecessorId])
            ->findOne();
        if ($successor) {
            throw new Conflict(
                'OptimizationInsight predecessor already has a successor.'
            );
        }
    }

    private function optionalId(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
