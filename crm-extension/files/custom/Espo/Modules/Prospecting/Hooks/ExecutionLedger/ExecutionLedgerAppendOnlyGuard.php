<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ExecutionLedger;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C22ExecutionSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for append-only C22 execution evidence.
 */
final class ExecutionLedgerAppendOnlyGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden(
                'ExecutionLedger is append-only and cannot be modified.'
            );
        }

        if (
            $options->get(
                C22ExecutionSaveOption::EXECUTION_LEDGER_CREATE_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'ExecutionLedger creation must use ExecutionLedgerService.'
            );
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden(
            'ExecutionLedger is append-only and cannot be deleted.'
        );
    }
}
