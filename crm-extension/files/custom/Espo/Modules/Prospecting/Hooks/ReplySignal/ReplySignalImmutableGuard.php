<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ReplySignal;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24ReplySignalSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/** Blocks direct ReplySignal edits and deletion. */
final class ReplySignalImmutableGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            if ($options->get(
                C24ReplySignalSaveOption::LIFECYCLE_MUTATION_AUTHORIZED
            ) !== true) {
                throw new Forbidden(
                    'ReplySignal mutation must use its governance service.'
                );
            }

            return;
        }
        if ($options->get(
            C24ReplySignalSaveOption::REPLY_SIGNAL_CREATE_AUTHORIZED
        ) !== true) {
            throw new Forbidden('ReplySignal creation must use its service.');
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('ReplySignal cannot be deleted.');
    }
}
