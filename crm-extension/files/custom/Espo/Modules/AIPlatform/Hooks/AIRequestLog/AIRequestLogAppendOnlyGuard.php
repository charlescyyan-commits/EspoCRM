<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Hooks\AIRequestLog;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\AIPlatform\Services\AIRequestLogSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for immutable AI execution evidence.
 */
final class AIRequestLogAppendOnlyGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (!$entity->isNew()) {
            throw new Forbidden('AIRequestLog is append-only and cannot be modified.');
        }

        $authorized = $options->get(
            AIRequestLogSaveOption::AI_REQUEST_LOG_CREATE_AUTHORIZED
        ) === true;
        if (!$authorized) {
            throw new Forbidden('AIRequestLog creation must use AIRequestLogService.');
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('AIRequestLog is append-only and cannot be deleted.');
    }
}
