<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\FeedbackLearningObservation;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C23FeedbackLearningSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/** Preserves each aggregate learning observation as immutable evidence. */
final class FeedbackLearningObservationImmutableGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden('FeedbackLearningObservation is immutable.');
        }
        if (
            $options->get(
                C23FeedbackLearningSaveOption::OBSERVATION_CREATE_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'FeedbackLearningObservation creation must use its service.'
            );
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('FeedbackLearningObservation cannot be deleted.');
    }
}
