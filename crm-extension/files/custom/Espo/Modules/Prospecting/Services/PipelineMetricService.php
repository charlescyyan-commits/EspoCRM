<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;

/** Validates and aggregates C24 commercial measurements for advisory analysis. */
final class PipelineMetricService
{
    /**
     * @param array<string, mixed> $metric
     * @return array{metricType: string, value: float, unit: string, reportingPeriod: string}
     */
    public function validateMetric(array $metric): array
    {
        $value = $metric['value'] ?? null;
        if ((!is_int($value) && !is_float($value)) || !is_finite((float) $value)) {
            throw new BadRequest('PipelineMetric requires a finite numeric value.');
        }

        return [
            'metricType' => $this->requiredText(
                $metric['metricType'] ?? null,
                'metricType'
            ),
            'value' => (float) $value,
            'unit' => $this->requiredText($metric['unit'] ?? null, 'unit'),
            'reportingPeriod' => $this->requiredText(
                $metric['reportingPeriod'] ?? null,
                'reportingPeriod'
            ),
        ];
    }

    /**
     * @param array<string, mixed> $metric
     * @return array{methodology: string, provenance: string}
     */
    public function validateProvenance(array $metric): array
    {
        return [
            'methodology' => $this->requiredText(
                $metric['methodology'] ?? null,
                'methodology'
            ),
            'provenance' => $this->requiredText(
                $metric['provenance'] ?? null,
                'provenance'
            ),
        ];
    }

    public function evaluateFreshness(mixed $value): string
    {
        if ($value === 'CURRENT') {
            return 'fresh';
        }
        if (in_array($value, ['AGING', 'STALE', 'ARCHIVAL'], true)) {
            return 'stale';
        }

        return 'unknown';
    }

    /**
     * @param list<array<string, mixed>> $metrics
     * @return array{metricType: string, unit: string, reportingPeriod: string, count: int, total: float, average: float, freshness: string}
     */
    public function aggregate(array $metrics): array
    {
        if ($metrics === []) {
            throw new BadRequest('PipelineMetric aggregation requires metrics.');
        }

        $first = $this->validateMetric($metrics[0]);
        $this->validateProvenance($metrics[0]);
        $total = $first['value'];
        $freshness = $this->evaluateFreshness(
            $metrics[0]['freshnessStatus'] ?? null
        );

        foreach (array_slice($metrics, 1) as $metric) {
            $validated = $this->validateMetric($metric);
            $this->validateProvenance($metric);
            if (
                $validated['metricType'] !== $first['metricType']
                || $validated['unit'] !== $first['unit']
                || $validated['reportingPeriod'] !== $first['reportingPeriod']
            ) {
                throw new BadRequest(
                    'PipelineMetric aggregation requires matching analytical dimensions.'
                );
            }
            $total += $validated['value'];
            if ($this->evaluateFreshness($metric['freshnessStatus'] ?? null) !== 'fresh') {
                $freshness = 'stale';
            }
        }

        $count = count($metrics);

        return [
            'metricType' => $first['metricType'],
            'unit' => $first['unit'],
            'reportingPeriod' => $first['reportingPeriod'],
            'count' => $count,
            'total' => $total,
            'average' => $total / $count,
            'freshness' => $freshness,
        ];
    }

    private function requiredText(mixed $value, string $field): string
    {
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("PipelineMetric requires {$field}.");
        }

        return trim($value);
    }
}
