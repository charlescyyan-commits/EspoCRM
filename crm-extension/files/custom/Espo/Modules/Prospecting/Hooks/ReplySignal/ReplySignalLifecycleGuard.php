<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ReplySignal;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24ReplySignalSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Enforces the human-governed ReplySignal lifecycle and append-only audit. */
final class ReplySignalLifecycleGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'RECEIVED' => ['INTERPRETED'],
        'INTERPRETED' => ['REVIEWED'],
        'REVIEWED' => ['CONVERTED', 'DISMISSED'],
        'CONVERTED' => [],
        'DISMISSED' => [],
    ];

    /** @var list<string> */
    private const SOURCE_FIELDS = [
        'name',
        'sourceReference',
        'provenance',
        'freshnessStatus',
        'createdAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if (
            $entity->isNew()
            || $options->get(
                C24ReplySignalSaveOption::LIFECYCLE_MUTATION_AUTHORIZED
            ) !== true
        ) {
            return;
        }
        foreach (self::SOURCE_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden("ReplySignal field {$field} is immutable.");
            }
        }
        if (!$entity->isAttributeChanged('status')) {
            throw new Forbidden('ReplySignal lifecycle mutation requires a status transition.');
        }

        $from = (string) $entity->getFetched('status');
        $to = (string) $entity->get('status');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden("ReplySignal transition {$from} to {$to} is forbidden.");
        }
        if ($from === 'RECEIVED') {
            if (
                !$entity->isAttributeChanged('interpretation')
                || !$entity->isAttributeChanged('confidence')
            ) {
                throw new Forbidden('ReplySignal interpretation requires content and confidence.');
            }
        } elseif (
            $entity->isAttributeChanged('interpretation')
            || $entity->isAttributeChanged('confidence')
        ) {
            throw new Forbidden('ReplySignal interpretation is immutable after interpretation.');
        }
        if (
            !$entity->isAttributeChanged('lifecycleAudit')
            || trim((string) $entity->get('transitionedAt')) === ''
            || trim((string) $entity->get('transitionedByReference')) === ''
        ) {
            throw new Forbidden('ReplySignal transition requires immutable audit provenance.');
        }
        if (
            $to === 'DISMISSED'
            && trim((string) $entity->get('decisionNote')) === ''
        ) {
            throw new Forbidden('Dismissed ReplySignal requires a decisionNote.');
        }
    }
}
