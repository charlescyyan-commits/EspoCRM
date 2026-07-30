<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal marker for human-governed OpportunityCandidate transitions. */
final class C24OpportunityCandidateSaveOption
{
    public const LIFECYCLE_TRANSITION_AUTHORIZED =
        'c24.opportunityCandidateLifecycleTransitionAuthorized';

    private function __construct()
    {
    }
}
