<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/**
 * Per-save authorization option names for status-owning domain services.
 *
 * These option values are intentionally scoped to one EntityManager save call.
 */
final class StatusMutationSaveOption
{
    public const QUOTE_STATUS_MUTATION_AUTHORIZED = 'prospecting.quoteStatusMutationAuthorized';
    public const APPROVAL_STATUS_MUTATION_AUTHORIZED = 'prospecting.approvalStatusMutationAuthorized';
}
