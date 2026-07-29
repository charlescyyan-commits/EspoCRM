<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\AIQualificationInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C21IntelligenceSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for immutable advisory insight history.
 */
final class AIQualificationInsightImmutableGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden(
                'AIQualificationInsight is immutable; create a superseding insight.'
            );
        }

        if (
            $options->get(
                C21IntelligenceSaveOption::INSIGHT_CREATE_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'AIQualificationInsight creation must use AIQualificationInsightService.'
            );
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden(
            'AIQualificationInsight history cannot be deleted.'
        );
    }
}
