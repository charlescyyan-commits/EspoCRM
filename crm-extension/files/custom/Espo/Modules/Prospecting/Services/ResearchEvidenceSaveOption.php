<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/**
 * Internal persistence authorization markers for ResearchEvidence governance.
 */
final class ResearchEvidenceSaveOption
{
    public const VALIDATION_MUTATION_AUTHORIZED =
        'c21.researchEvidenceValidationMutationAuthorized';
    public const LEGACY_CLASSIFICATION_AUTHORIZED =
        'c21.researchEvidenceLegacyClassificationAuthorized';
    public const LEAD_ATTACHMENT_AUTHORIZED =
        'c21.researchEvidenceLeadAttachmentAuthorized';
    public const CORRECTION_CREATE_AUTHORIZED =
        'c21.researchEvidenceCorrectionCreateAuthorized';

    private function __construct()
    {
    }
}
