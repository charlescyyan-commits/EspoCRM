<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Provenance validator for WP4 Commercial Decision Support artifacts.
 *
 * Consumes C20 Package A capability identity by reference only.
 * Does not authorize provider invocation or C20 registry changes.
 */
final class DecisionSupportProvenanceValidator
{
    public const CAPABILITY_COMMERCIAL_BRIEF = 'COMMERCIAL_BRIEF';
    public const PURPOSE_COMMERCIAL_DECISION_SUPPORT = 'commercial_decision_support';

    /**
     * @param array{
     *   sourceEvidenceReference?: mixed,
     *   capabilityReference?: mixed,
     *   purposeReference?: mixed
     * } $fields
     */
    public function assertComplete(array $fields): void
    {
        $evidence = trim((string) ($fields['sourceEvidenceReference'] ?? ''));
        $capability = trim((string) ($fields['capabilityReference'] ?? ''));
        $purpose = trim((string) ($fields['purposeReference'] ?? ''));

        if ($evidence === '') {
            throw new BadRequest(
                'WP4 Decision Support artifact requires sourceEvidenceReference.'
            );
        }
        if ($capability !== self::CAPABILITY_COMMERCIAL_BRIEF) {
            throw new BadRequest(
                'WP4 capabilityReference must be COMMERCIAL_BRIEF (consumed identity).'
            );
        }
        if ($purpose !== self::PURPOSE_COMMERCIAL_DECISION_SUPPORT) {
            throw new BadRequest(
                'WP4 purposeReference must be commercial_decision_support.'
            );
        }
    }
}
