<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Provenance completeness for CommercialBrief acceptance governance.
 *
 * Provenance is a C20 identity/policy consumption contract — not a runtime
 * invocation license.
 */
final class BriefProvenanceValidator
{
    public const CAPABILITY_COMMERCIAL_BRIEF = 'COMMERCIAL_BRIEF';
    public const PURPOSE_COMMERCIAL_BRIEF_GENERATION = 'commercial_brief_generation';

    /**
     * @param array{
     *   sourceEvidenceReference?: mixed,
     *   generationContext?: mixed,
     *   capabilityReference?: mixed,
     *   purposeReference?: mixed
     * } $fields
     */
    public function assertComplete(array $fields): void
    {
        $evidence = trim((string) ($fields['sourceEvidenceReference'] ?? ''));
        $context = trim((string) ($fields['generationContext'] ?? ''));
        $capability = trim((string) ($fields['capabilityReference'] ?? ''));
        $purpose = trim((string) ($fields['purposeReference'] ?? ''));

        if ($evidence === '') {
            throw new BadRequest('CommercialBrief requires sourceEvidenceReference.');
        }
        if ($context === '') {
            throw new BadRequest('CommercialBrief requires generationContext.');
        }
        if ($capability !== self::CAPABILITY_COMMERCIAL_BRIEF) {
            throw new BadRequest(
                'CommercialBrief capabilityReference must be COMMERCIAL_BRIEF.'
            );
        }
        if ($purpose !== self::PURPOSE_COMMERCIAL_BRIEF_GENERATION) {
            throw new BadRequest(
                'CommercialBrief purposeReference must be commercial_brief_generation.'
            );
        }
    }
}
