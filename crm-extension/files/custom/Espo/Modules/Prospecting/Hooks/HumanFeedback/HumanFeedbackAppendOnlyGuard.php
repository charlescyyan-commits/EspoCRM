<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\HumanFeedback;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C21IntelligenceSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for append-only human review signals.
 */
final class HumanFeedbackAppendOnlyGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden(
                'HumanFeedback is append-only and cannot be modified.'
            );
        }

        if (
            $options->get(
                C21IntelligenceSaveOption::HUMAN_FEEDBACK_CREATE_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'HumanFeedback creation must use HumanFeedbackService.'
            );
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden(
            'HumanFeedback is append-only and cannot be deleted.'
        );
    }
}
