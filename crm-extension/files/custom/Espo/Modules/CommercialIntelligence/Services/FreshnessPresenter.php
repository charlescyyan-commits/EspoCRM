<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Modules\CommercialIntelligence\Context\SourceArtifactReference;

/**
 * Freshness surfacing (ADR-C25-005 §5; C24-INV-REV-005).
 *
 * Pass-through only: C25 does not alter, extend, or reset any source
 * artifact's freshness state. STALE and ARCHIVAL warnings MUST be
 * surfaced, never suppressed.
 */
final class FreshnessPresenter
{
    public const WARNING_STATES = ['STALE', 'ARCHIVAL'];

    /** @return array<string, mixed> */
    public function present(SourceArtifactReference $reference): array
    {
        $status = $reference->freshnessStatus;

        return [
            'stalenessWarning' => $status !== null
                && in_array($status, self::WARNING_STATES, true),
            'warningLabel' => $this->warningLabel($status),
        ];
    }

    private function warningLabel(?string $status): ?string
    {
        return match ($status) {
            'STALE' => 'Stale — for historical reference only',
            'ARCHIVAL' => 'Archival — retained for audit; do not use for current decisions',
            default => null,
        };
    }
}
