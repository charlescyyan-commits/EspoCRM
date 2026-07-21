<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\Approval;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\StatusMutationSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Terminal persistence boundary for Approval.status and Approval creation.
 */
class ApprovalStatusMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($options->get(StatusMutationSaveOption::APPROVAL_STATUS_MUTATION_AUTHORIZED) === true) {
            return;
        }

        if (!$entity->isNew() && !$entity->isAttributeChanged('status')) {
            return;
        }

        throw new Forbidden('Approval status mutation must use ApprovalService.');
    }
}
