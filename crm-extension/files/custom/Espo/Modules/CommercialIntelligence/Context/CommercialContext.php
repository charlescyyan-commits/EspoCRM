<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Context;

/**
 * CommercialContext — runtime read model (ADR-C25-001 §3–§5).
 *
 * CommercialContext MUST remain a runtime read model only.
 * It MUST NOT become:
 *
 *   - a persistent entity
 *   - a database table
 *   - a CRM object
 *   - a lifecycle artifact
 *
 * It is assembled per explicit human request, rendered, and discarded. It
 * has no lifecycle, no state machine, and no mutation path. It is not an
 * ORM object and has no persistence adapter of any kind.
 */
final class CommercialContext
{
    public const ASSEMBLY_VERSION = 'c25-wp1-assembly-v1';

    public const ADVISORY_DESIGNATION =
        'AI-assembled commercial context — for human review only. '
        . 'Not a decision, forecast, or commitment.';

    public const ASSEMBLED_MARKER = 'AI_ASSEMBLED_CONTEXT';

    /** @var array<string, list<array<string, mixed>>> */
    private array $sections = [];

    /** @var array<string, string|null>|null */
    private ?array $anchor = null;

    private readonly string $assembledAt;

    public function __construct()
    {
        $this->assembledAt = gmdate('Y-m-d\TH:i:s\Z');
    }

    public function setAnchor(string $entityType, string $entityId, ?string $displayName): void
    {
        $this->anchor = [
            'entityType' => $entityType,
            'entityId' => $entityId,
            'displayName' => $displayName,
        ];
    }

    /**
     * @param array<string, mixed> $freshnessPresentation
     */
    public function addArtifact(
        string $section,
        SourceArtifactReference $reference,
        array $freshnessPresentation
    ): void {
        $this->sections[$section][] = array_merge(
            $reference->toArray(),
            $freshnessPresentation
        );
    }

    /** @return array<string, mixed> */
    public function toArray(): array
    {
        return [
            'anchor' => $this->anchor,
            'assembledAt' => $this->assembledAt,
            'assemblyVersion' => self::ASSEMBLY_VERSION,
            'advisoryDesignation' => self::ADVISORY_DESIGNATION,
            'assembledMarker' => self::ASSEMBLED_MARKER,
            'sections' => $this->sections,
            'freshnessSummary' => $this->freshnessSummary(),
        ];
    }

    /**
     * Display summary of passed-through freshness states. Counts only;
     * no source freshness state is altered, extended, or reset.
     *
     * @return array<string, int>
     */
    private function freshnessSummary(): array
    {
        $summary = [
            'CURRENT' => 0,
            'AGING' => 0,
            'STALE' => 0,
            'ARCHIVAL' => 0,
            'UNKNOWN' => 0,
        ];

        foreach ($this->sections as $references) {
            foreach ($references as $reference) {
                $status = $reference['freshnessStatus'] ?? null;
                if (!is_string($status) || !array_key_exists($status, $summary)) {
                    $summary['UNKNOWN']++;
                    continue;
                }
                $summary[$status]++;
            }
        }

        return $summary;
    }
}
