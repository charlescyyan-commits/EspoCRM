<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\OptimizationInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C23AnalyticsSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/** Prevents direct mutation of an advisory C23 record. */
final class OptimizationInsightImmutableGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden('OptimizationInsight is immutable.');
        }
        if ($options->get(C23AnalyticsSaveOption::OPTIMIZATION_INSIGHT_CREATE_AUTHORIZED) !== true) {
            throw new Forbidden('OptimizationInsight creation must use its service.');
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('OptimizationInsight cannot be deleted.');
    }
}
