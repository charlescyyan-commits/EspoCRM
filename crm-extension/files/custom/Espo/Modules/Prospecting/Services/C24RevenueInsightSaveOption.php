<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Save-option keys reserved for a future human RevenueInsight lifecycle service. */
final class C24RevenueInsightSaveOption
{
    public const LIFECYCLE_TRANSITION_AUTHORIZED =
        'c24.revenueInsightLifecycleTransitionAuthorized';
    public const LIFECYCLE_ACTOR_REFERENCE =
        'c24.revenueInsightLifecycleActorReference';
    public const LIFECYCLE_TRANSITION_REASON =
        'c24.revenueInsightLifecycleTransitionReason';
    public const LIFECYCLE_TRANSITION_TIMESTAMP =
        'c24.revenueInsightLifecycleTransitionTimestamp';

    private function __construct()
    {
    }
}
