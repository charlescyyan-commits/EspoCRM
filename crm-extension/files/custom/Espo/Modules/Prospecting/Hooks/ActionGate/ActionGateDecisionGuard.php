<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ActionGate;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C22ExecutionSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Prevents direct creation, decision changes, identity changes, and deletion.
 */
final class ActionGateDecisionGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_FIELDS = [
        'name',
        'prospectCandidateId',
        'prospectRunId',
        'actionType',
        'actionReference',
        'requestedById',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(
                    C22ExecutionSaveOption::ACTION_GATE_CREATE_AUTHORIZED
                ) !== true
            ) {
                throw new Forbidden(
                    'ActionGate creation must use ActionGateService.'
                );
            }

            return;
        }

        if (
            $options->get(
                C22ExecutionSaveOption::ACTION_GATE_DECISION_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'ActionGate decision must use ActionGateService.'
            );
        }
        foreach (self::IMMUTABLE_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "ActionGate immutable field {$field} cannot be modified."
                );
            }
        }
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden('ActionGate cannot be deleted.');
    }
}
