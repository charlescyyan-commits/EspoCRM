<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\PerformanceMetric;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C23AnalyticsSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/** Preserves PerformanceMetric as point-in-time reporting evidence. */
final class PerformanceMetricImmutableGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden('PerformanceMetric is immutable.');
        }
        if ($options->get(C23AnalyticsSaveOption::PERFORMANCE_METRIC_CREATE_AUTHORIZED) !== true) {
            throw new Forbidden('PerformanceMetric creation must use its service.');
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('PerformanceMetric cannot be deleted.');
    }
}
