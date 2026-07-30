<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal write marker for governed OptimizationInsight lifecycle changes. */
final class C23OptimizationInsightLifecycleSaveOption
{
    public const LIFECYCLE_MUTATION_AUTHORIZED =
        'c23.optimizationInsightLifecycleMutationAuthorized';

    private function __construct()
    {
    }
}
