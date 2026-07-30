<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal write markers for the C23 analytics governance boundary. */
final class C23AnalyticsSaveOption
{
    public const OPTIMIZATION_INSIGHT_CREATE_AUTHORIZED =
        'c23.optimizationInsightCreateAuthorized';
    public const PERFORMANCE_METRIC_CREATE_AUTHORIZED =
        'c23.performanceMetricCreateAuthorized';

    private function __construct()
    {
    }
}
