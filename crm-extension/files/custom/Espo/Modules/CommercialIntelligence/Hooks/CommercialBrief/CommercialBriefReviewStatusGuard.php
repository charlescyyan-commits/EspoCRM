<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\CommercialBrief;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\CommercialBriefSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Enforces closed CommercialBrief reviewStatus transitions. */
final class CommercialBriefReviewStatusGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'GENERATED' => ['REVIEWED'],
        'REVIEWED' => ['ACCEPTED', 'DISMISSED'],
        'ACCEPTED' => [],
        'DISMISSED' => [],
    ];

    /** @var list<string> */
    private const LIFECYCLE_FIELDS = [
        'reviewStatus',
        'transitionHistory',
        'lastTransitionBy',
        'lastTransitionAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            $status = (string) $entity->get('reviewStatus');
            if ($status !== '' && $status !== 'GENERATED') {
                throw new Forbidden(
                    'CommercialBrief may only be created in GENERATED status.'
                );
            }

            return;
        }

        $hasLifecycleMutation = false;
        foreach (self::LIFECYCLE_FIELDS as $field) {
            $hasLifecycleMutation = $hasLifecycleMutation
                || $entity->isAttributeChanged($field);
        }
        if (!$hasLifecycleMutation) {
            return;
        }

        if (
            $options->get(CommercialBriefSaveOption::REVIEW_TRANSITION_AUTHORIZED)
            !== true
        ) {
            throw new Forbidden(
                'CommercialBrief review mutation must use CommercialBriefReviewService.'
            );
        }

        foreach (self::LIFECYCLE_FIELDS as $field) {
            if (!$entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "CommercialBrief transition requires {$field}."
                );
            }
        }

        $from = (string) $entity->getFetched('reviewStatus');
        $to = (string) $entity->get('reviewStatus');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "CommercialBrief transition {$from} to {$to} is forbidden."
            );
        }

        $this->assertAuditAppend($entity, $from, $to);
    }

    private function assertAuditAppend(Entity $entity, string $from, string $to): void
    {
        $previous = $this->history($entity->getFetched('transitionHistory'));
        $current = $this->history($entity->get('transitionHistory'));
        if (
            count($current) !== count($previous) + 1
            || array_slice($current, 0, count($previous)) !== $previous
        ) {
            throw new Forbidden(
                'CommercialBrief transitionHistory must append one immutable record.'
            );
        }

        $record = $current[array_key_last($current)];
        if (!is_array($record)) {
            throw new Forbidden('CommercialBrief transition audit is invalid.');
        }

        $actor = $record['actorReference'] ?? null;
        $actorKind = $record['actorKind'] ?? null;
        $timestamp = $record['transitionedAt'] ?? null;
        $reason = $record['transitionReason'] ?? null;
        if (
            ($record['fromStatus'] ?? null) !== $from
            || ($record['toStatus'] ?? null) !== $to
            || $actorKind !== 'HUMAN'
            || !is_string($actor)
            || trim($actor) === ''
            || !is_string($timestamp)
            || trim($timestamp) === ''
            || !is_string($reason)
            || trim($reason) === ''
        ) {
            throw new Forbidden(
                'CommercialBrief transition requires human actor audit fields.'
            );
        }
    }

    /** @return list<mixed> */
    private function history(mixed $value): array
    {
        if ($value === null || trim((string) $value) === '') {
            return [];
        }
        if (!is_string($value)) {
            return [];
        }
        try {
            $decoded = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            return [];
        }

        return is_array($decoded) && array_is_list($decoded) ? $decoded : [];
    }
}
