<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates and reads immutable, aggregate C23 measurement artifacts.
 *
 * The service stores analytical inputs by reference only. It has no authority
 * over execution, approvals, source records, or CRM workflow state.
 */
final class PerformanceMetricService
{
    public const ENTITY_TYPE = 'PerformanceMetric';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'metricType',
        'metricValue',
        'aggregationPeriod',
        'sampleSize',
        'confidenceLevel',
        'freshnessStatus',
        'sourceReference',
        'generatedAt',
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
        $metric = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $metric->set([
            'name' => 'Performance Metric: ' . $attributes['metricType'],
            ...$attributes,
        ]);

        $this->entityManager->saveEntity($metric, [
            C23AnalyticsSaveOption::PERFORMANCE_METRIC_CREATE_AUTHORIZED => true,
        ]);

        return $metric;
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $metric = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$metric || $metric->isNew()) {
            throw new BadRequest('PerformanceMetric does not exist.');
        }
        if (!$this->acl->checkEntityRead($metric)) {
            throw new Forbidden();
        }

        return $metric;
    }

    /**
     * @param array<string, mixed> $attributes
     * @return array<string, mixed>
     */
    public function validate(array $attributes): array
    {
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest('PerformanceMetric contains unsupported fields.');
        }

        return [
            'metricType' => $this->requiredText($attributes, 'metricType'),
            'metricValue' => $this->metricValue(
                $attributes['metricValue'] ?? null
            ),
            'aggregationPeriod' => json_encode(
                $this->aggregationPeriod($attributes['aggregationPeriod'] ?? null),
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'sampleSize' => $this->sampleSize($attributes['sampleSize'] ?? null),
            'confidenceLevel' => $this->confidenceLevel(
                $attributes['confidenceLevel'] ?? null
            ),
            'freshnessStatus' => $this->freshnessStatus(
                $attributes['freshnessStatus'] ?? null
            ),
            'sourceReference' => json_encode(
                $this->aggregateReferences(
                    $attributes['sourceReference'] ?? null
                ),
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'generatedAt' => $this->requiredDate(
                $attributes,
                'generatedAt'
            )->format('Y-m-d H:i:s'),
        ];
    }

    /** @return array{start: string, end: string} */
    private function aggregationPeriod(mixed $value): array
    {
        if (!is_array($value)) {
            throw new BadRequest('PerformanceMetric aggregationPeriod must be an object.');
        }
        $start = $this->requiredDate($value, 'start');
        $end = $this->requiredDate($value, 'end');
        if ($start > $end) {
            throw new BadRequest(
                'PerformanceMetric aggregationPeriod must be chronological.'
            );
        }

        return [
            'start' => $start->format('Y-m-d H:i:s'),
            'end' => $end->format('Y-m-d H:i:s'),
        ];
    }

    /** @return list<array{entityType: string, reference: string}> */
    private function aggregateReferences(mixed $value): array
    {
        if (!is_array($value) || $value === [] || count($value) > 100) {
            throw new BadRequest(
                'PerformanceMetric sourceReference requires 1 to 100 references.'
            );
        }

        $references = [];
        foreach ($value as $reference) {
            if (!is_array($reference)) {
                throw new BadRequest(
                    'PerformanceMetric sourceReference must contain reference objects.'
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
                    'PerformanceMetric sourceReference contains an invalid aggregate reference.'
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
            throw new BadRequest("PerformanceMetric requires {$field}.");
        }

        return trim($value);
    }

    /** @param array<string, mixed> $attributes */
    private function requiredDate(array $attributes, string $field): DateTimeImmutable
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("PerformanceMetric requires {$field}.");
        }
        try {
            return new DateTimeImmutable($value);
        } catch (\Exception) {
            throw new BadRequest("PerformanceMetric {$field} must be a date.");
        }
    }

    private function metricValue(mixed $value): float
    {
        if (!is_int($value) && !is_float($value)) {
            throw new BadRequest('PerformanceMetric metricValue must be numeric.');
        }

        return (float) $value;
    }

    private function sampleSize(mixed $value): int
    {
        if (!is_int($value) || $value < 1) {
            throw new BadRequest('PerformanceMetric sampleSize must be a positive integer.');
        }

        return $value;
    }

    private function confidenceLevel(mixed $value): float
    {
        if (
            (!is_int($value) && !is_float($value))
            || $value < 0
            || $value > 1
        ) {
            throw new BadRequest(
                'PerformanceMetric confidenceLevel must be between 0 and 1.'
            );
        }

        return (float) $value;
    }

    private function freshnessStatus(mixed $value): string
    {
        if (!is_string($value) || !in_array($value, self::FRESHNESS_STATUSES, true)) {
            throw new BadRequest('PerformanceMetric has an invalid freshnessStatus.');
        }

        return $value;
    }
}
