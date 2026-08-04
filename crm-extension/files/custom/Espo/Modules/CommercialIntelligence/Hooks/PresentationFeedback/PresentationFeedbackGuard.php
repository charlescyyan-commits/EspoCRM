<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\PresentationFeedback;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp4DecisionSupportSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** PresentationFeedback is create-once; no training/optimization mutation paths. */
final class PresentationFeedbackGuard implements BeforeSave
{
    public static int $order = 1010;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(Wp4DecisionSupportSaveOption::FEEDBACK_CREATE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'PresentationFeedback create must use PresentationFeedbackService.'
                );
            }

            return;
        }

        throw new Forbidden(
            'PresentationFeedback is immutable after create; no training or optimization updates.'
        );
    }
}
