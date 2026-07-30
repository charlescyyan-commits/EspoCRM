<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal marker for a future integrity-controlled PipelineMetric update. */
final class C24PipelineMetricSaveOption
{
    public const INTEGRITY_UPDATE_AUTHORIZED =
        'c24.pipelineMetricIntegrityUpdateAuthorized';

    private function __construct()
    {
    }
}
