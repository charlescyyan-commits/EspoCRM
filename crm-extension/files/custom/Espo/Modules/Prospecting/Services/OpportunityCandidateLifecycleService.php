<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/** Human-governed lifecycle boundary for a C24 governance record. */
final class OpportunityCandidateLifecycleService
{
    public const ENTITY_TYPE = 'OpportunityCandidate';
    public const STATUS_IDENTIFIED = 'IDENTIFIED';
    public const STATUS_REVIEW_PENDING = 'REVIEW_PENDING';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_ACTIVE = 'ACTIVE';
    public const STATUS_WON = 'WON';
    public const STATUS_LOST = 'LOST';
    public const STATUS_REJECTED = 'REJECTED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {
    }

    public function submitForReview(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_IDENTIFIED,
            self::STATUS_REVIEW_PENDING,
            $reason
        );
    }

    public function accept(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEW_PENDING,
            self::STATUS_ACCEPTED,
            $reason
        );
    }

    public function reject(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEW_PENDING,
            self::STATUS_REJECTED,
            $reason
        );
    }

    public function activate(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_ACCEPTED,
            self::STATUS_ACTIVE,
            $reason
        );
    }

    public function recordWon(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_ACTIVE,
            self::STATUS_WON,
            $reason
        );
    }

    public function recordLost(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_ACTIVE,
            self::STATUS_LOST,
            $reason
        );
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $candidate = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$candidate || $candidate->isNew()) {
            throw new BadRequest('OpportunityCandidate does not exist.');
        }
        if (!$this->acl->checkEntityRead($candidate)) {
            throw new Forbidden();
        }

        return $candidate;
    }

    private function transition(
        string $id,
        string $expectedStatus,
        string $targetStatus,
        string $reason
    ): Entity {
        $candidate = $this->read($id);
        if ((string) $candidate->get('status') !== $expectedStatus) {
            throw new Conflict(
                "OpportunityCandidate must be {$expectedStatus} before {$targetStatus}."
            );
        }

        $actor = $this->authenticatedHumanReference();
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s');
        $history = $this->transitionHistory($candidate);
        $history[] = [
            'fromStatus' => $expectedStatus,
            'toStatus' => $targetStatus,
            'actorReference' => $actor,
            'transitionedAt' => $timestamp,
            'transitionReason' => $this->requiredReason($reason),
        ];
        $candidate->set([
            'status' => $targetStatus,
            'lastTransitionBy' => $actor,
            'lastTransitionAt' => $timestamp,
            'transitionHistory' => json_encode(
                $history,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
        ]);
        $this->entityManager->saveEntity($candidate, [
            C24OpportunityCandidateSaveOption::LIFECYCLE_TRANSITION_AUTHORIZED => true,
        ]);

        return $candidate;
    }

    /** @return list<array<string, mixed>> */
    private function transitionHistory(Entity $candidate): array
    {
        $value = $candidate->get('transitionHistory');
        if ($value === null || trim((string) $value) === '') {
            return [];
        }
        if (!is_string($value)) {
            throw new Conflict('OpportunityCandidate transitionHistory is invalid.');
        }
        try {
            $history = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Conflict('OpportunityCandidate transitionHistory is invalid.');
        }
        if (!is_array($history) || !array_is_list($history)) {
            throw new Conflict('OpportunityCandidate transitionHistory is invalid.');
        }

        return $history;
    }

    private function authenticatedHumanReference(): string
    {
        $reference = trim((string) $this->user->getId());
        if ($reference === '') {
            throw new Forbidden(
                'OpportunityCandidate transition requires an authenticated human actor.'
            );
        }

        return $reference;
    }

    private function requiredReason(string $reason): string
    {
        $reason = trim($reason);
        if ($reason === '') {
            throw new BadRequest('OpportunityCandidate transition requires a reason.');
        }

        return $reason;
    }
}
