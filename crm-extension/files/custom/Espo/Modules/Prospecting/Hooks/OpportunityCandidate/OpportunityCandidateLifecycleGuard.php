<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\OpportunityCandidate;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24OpportunityCandidateSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Enforces closed, human-audited OpportunityCandidate status transitions. */
final class OpportunityCandidateLifecycleGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'IDENTIFIED' => ['REVIEW_PENDING'],
        'REVIEW_PENDING' => ['ACCEPTED', 'REJECTED'],
        'ACCEPTED' => ['ACTIVE'],
        'ACTIVE' => ['WON', 'LOST'],
        'WON' => [],
        'LOST' => [],
        'REJECTED' => [],
    ];

    /** @var list<string> */
    private const LIFECYCLE_FIELDS = [
        'status',
        'transitionHistory',
        'lastTransitionBy',
        'lastTransitionAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
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
        if ($options->get(
            C24OpportunityCandidateSaveOption::LIFECYCLE_TRANSITION_AUTHORIZED
        ) !== true) {
            throw new Forbidden(
                'OpportunityCandidate lifecycle mutation must use its lifecycle service.'
            );
        }
        foreach (self::LIFECYCLE_FIELDS as $field) {
            if (!$entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "OpportunityCandidate transition requires {$field}."
                );
            }
        }

        $from = (string) $entity->getFetched('status');
        $to = (string) $entity->get('status');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "OpportunityCandidate transition {$from} to {$to} is forbidden."
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
                'OpportunityCandidate transitionHistory must append one immutable record.'
            );
        }
        $record = $current[array_key_last($current)];
        if (!is_array($record)) {
            throw new Forbidden('OpportunityCandidate transition audit is invalid.');
        }
        $actor = $record['actorReference'] ?? null;
        $timestamp = $record['transitionedAt'] ?? null;
        $reason = $record['transitionReason'] ?? null;
        if (
            ($record['fromStatus'] ?? null) !== $from
            || ($record['toStatus'] ?? null) !== $to
            || !is_string($actor)
            || trim($actor) === ''
            || !is_string($timestamp)
            || trim($timestamp) === ''
            || !is_string($reason)
            || trim($reason) === ''
            || $actor !== (string) $entity->get('lastTransitionBy')
            || $timestamp !== (string) $entity->get('lastTransitionAt')
        ) {
            throw new Forbidden(
                'OpportunityCandidate transition requires human audit provenance.'
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
            throw new Forbidden('OpportunityCandidate transitionHistory is invalid.');
        }
        try {
            $history = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Forbidden('OpportunityCandidate transitionHistory is invalid.');
        }
        if (!is_array($history) || !array_is_list($history)) {
            throw new Forbidden('OpportunityCandidate transitionHistory is invalid.');
        }

        return $history;
    }
}
