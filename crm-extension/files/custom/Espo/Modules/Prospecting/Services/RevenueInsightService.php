<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;

/** Builds read-only advisory context for a C24 commercial analysis record. */
final class RevenueInsightService
{
    /**
     * @param array<string, mixed> $insight
     * @return array<string, mixed>
     */
    public function assembleContext(array $insight): array
    {
        $provenance = $this->validateProvenance($insight);

        return [
            'interpretationContext' => $this->optionalText(
                $insight['interpretation'] ?? null
            ),
            'metricExplanation' => $this->metricExplanation(
                $provenance['metricReferences']
            ),
            'reviewContext' => $this->prepareAdvisorySummary($insight),
            'freshness' => $this->evaluateFreshness(
                $insight['freshnessStatus'] ?? null
            ),
            'sourceReference' => $provenance['sourceReference'],
            'provenance' => $provenance['provenance'],
        ];
    }

    /**
     * @param array<string, mixed> $insight
     * @return array{sourceReference: string, provenance: string, metricReferences: list<string>}
     */
    public function validateProvenance(array $insight): array
    {
        return [
            'sourceReference' => $this->requiredText(
                $insight['sourceReference'] ?? null,
                'sourceReference'
            ),
            'provenance' => $this->requiredText(
                $insight['provenance'] ?? null,
                'provenance'
            ),
            'metricReferences' => $this->metricReferences(
                $insight['metricReferences'] ?? null
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

    /** @param array<string, mixed> $insight */
    public function prepareAdvisorySummary(array $insight): string
    {
        $summary = $this->requiredText(
            $insight['insightSummary'] ?? null,
            'insightSummary'
        );
        $interpretation = $this->optionalText(
            $insight['interpretation'] ?? null
        );

        return $interpretation === null
            ? $summary
            : $summary . "\n\n" . $interpretation;
    }

    /** @return list<string> */
    private function metricReferences(mixed $value): array
    {
        if ($value === null || $value === '') {
            return [];
        }
        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                return [];
            }

            return [$value];
        }
        if (!is_array($value)) {
            throw new BadRequest('RevenueInsight metricReferences must be traceable.');
        }

        $references = [];
        foreach ($value as $reference) {
            if (!is_string($reference) || trim($reference) === '') {
                throw new BadRequest(
                    'RevenueInsight metricReferences must be traceable.'
                );
            }
            $references[] = trim($reference);
        }

        return $references;
    }

    /** @param list<string> $references */
    private function metricExplanation(array $references): string
    {
        if ($references === []) {
            return 'No metric reference was supplied.';
        }

        return 'Analytical metric references: ' . implode(', ', $references);
    }

    private function requiredText(mixed $value, string $field): string
    {
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("RevenueInsight requires {$field}.");
        }

        return trim($value);
    }

    private function optionalText(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
