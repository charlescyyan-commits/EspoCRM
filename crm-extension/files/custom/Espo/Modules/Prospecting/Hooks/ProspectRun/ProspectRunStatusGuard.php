<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ProspectRun;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C22ExecutionSaveOption;
use Espo\Modules\Prospecting\Services\ProspectRunLifecycleService;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Prevents direct ProspectRun status mutation outside its lifecycle service.
 */
final class ProspectRunStatusGuard implements BeforeSave
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            $status = (string) (
                $entity->get('status')
                ?: ProspectRunLifecycleService::STATUS_CREATED
            );
            if ($status !== ProspectRunLifecycleService::STATUS_CREATED) {
                throw new Forbidden(
                    'A new ProspectRun must start in CREATED.'
                );
            }

            return;
        }

        if (
            $entity->isAttributeChanged('status')
            && $options->get(
                C22ExecutionSaveOption::PROSPECT_RUN_STATUS_MUTATION_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'ProspectRun status must use ProspectRunLifecycleService.'
            );
        }
    }
}
