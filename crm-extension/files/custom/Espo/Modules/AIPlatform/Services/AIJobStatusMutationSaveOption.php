<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * Per-save authorization marker for AIJob lifecycle mutations.
 *
 * Its scope is one EntityManager save operation. It does not authorize a
 * dispatch, retry worker, or external execution.
 */
final class AIJobStatusMutationSaveOption
{
    public const AI_JOB_STATUS_MUTATION_AUTHORIZED = 'aiplatform.aiJobStatusMutationAuthorized';
}
