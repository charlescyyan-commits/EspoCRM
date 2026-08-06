<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

/**
 * Internal save-option markers for CommercialBrief mutation channels.
 *
 * Tokens are per field-set channel (Plan §20.3). AUDIT_WRITE_AUTHORIZED is
 * declared here per ADR-C25-007; the audit writer itself is WP2.3.
 */
final class CommercialBriefSaveOption
{
    public const GENERATION_AUTHORIZED = 'c25.briefGenerationAuthorized';

    public const STATUS_MUTATION_AUTHORIZED = 'c25.briefStatusMutationAuthorized';

    public const VALIDITY_DISPOSITION_AUTHORIZED =
        'c25.briefValidityDispositionAuthorized';

    public const RETENTION_DISPOSITION_AUTHORIZED =
        'c25.briefRetentionDispositionAuthorized';

    public const DELETION_AUTHORIZED = 'c25.briefDeletionAuthorized';

    public const AUDIT_WRITE_AUTHORIZED = 'c25.briefAuditWriteAuthorized';

    private function __construct()
    {
    }
}
