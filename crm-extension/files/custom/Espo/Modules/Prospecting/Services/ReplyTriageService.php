<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Sole writer of ReplyEvent triage lifecycle fields (ADR-C19 / adr-c19-replyevent-v1).
 *
 * Owns triageStatus plus the closedReason / closedAt / closedBy audit fields.
 * Provider facts (replyStatus, externalEventId, receivedAt) are ingress-owned
 * create-time facts and are never written here.
 */
class ReplyTriageService
{
    public const TRIAGE_OPEN = 'OPEN';
    public const TRIAGE_IN_PROGRESS = 'IN_PROGRESS';
    public const TRIAGE_CLOSED = 'CLOSED';

    public const ACTION_ASSIGN = 'replyEvent.assign';
    public const ACTION_RELEASE = 'replyEvent.release';
    public const ACTION_CLOSE = 'replyEvent.close';

    public const GOVERNANCE_MARKER = 'adr-c19-replyevent-v1';

    /** @var array<string, list<string>> */
    private const VALID_TRANSITIONS = [
        self::TRIAGE_OPEN => [self::TRIAGE_IN_PROGRESS, self::TRIAGE_CLOSED],
        self::TRIAGE_IN_PROGRESS => [self::TRIAGE_OPEN, self::TRIAGE_CLOSED],
        self::TRIAGE_CLOSED => [],
    ];

    /** @var array<string, array<string, string>> */
    private const TRANSITION_ACTIONS = [
        self::TRIAGE_OPEN => [
            self::TRIAGE_IN_PROGRESS => self::ACTION_ASSIGN,
            self::TRIAGE_CLOSED => self::ACTION_CLOSE,
        ],
        self::TRIAGE_IN_PROGRESS => [
            self::TRIAGE_OPEN => self::ACTION_RELEASE,
            self::TRIAGE_CLOSED => self::ACTION_CLOSE,
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {}

    public function validateTransition(string $currentStatus, string $targetStatus): bool
    {
        $this->assertKnownStatus($currentStatus);
        $this->assertKnownStatus($targetStatus);

        return in_array($targetStatus, self::VALID_TRANSITIONS[$currentStatus], true);
    }

    /**
     * Resolves the ADR action key required for a triage edge.
     */
    public function resolveAction(string $currentStatus, string $targetStatus): string
    {
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("ReplyEvent triage transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        $action = self::TRANSITION_ACTIONS[$currentStatus][$targetStatus] ?? null;
        if (!is_string($action) || $action === '') {
            throw new BadRequest("ReplyEvent triage transition {$currentStatus} -> {$targetStatus} has no authorization action.");
        }

        return $action;
    }

    /**
     * Authorizes a triage action for the current user against the reply event.
     */
    public function authorize(Entity $replyEvent, string $action): void
    {
        if ($replyEvent->getEntityType() !== 'ReplyEvent') {
            throw new BadRequest('ReplyEvent triage transition requires a ReplyEvent entity.');
        }

        if (!$this->acl->checkEntityEdit($replyEvent)) {
            throw new Forbidden();
        }

        $knownActions = [
            self::ACTION_ASSIGN,
            self::ACTION_RELEASE,
            self::ACTION_CLOSE,
        ];
        if (!in_array($action, $knownActions, true)) {
            throw new BadRequest('Unsupported ReplyEvent triage action.');
        }

        // WP1 foundation: edit ACL + known action key. Role bindings land with
        // metadata policy under GOVERNANCE_MARKER in a later WP.
        if ($this->user->isAdmin()) {
            return;
        }
    }

    /**
     * @param array{
     *   reason?: string|null,
     *   now?: DateTimeImmutable|string,
     *   skipAuthorization?: bool
     * } $options
     */
    public function transition(Entity $replyEvent, string $targetStatus, array $options = []): Entity
    {
        if ($replyEvent->getEntityType() !== 'ReplyEvent') {
            throw new BadRequest('ReplyEvent triage transition requires a ReplyEvent entity.');
        }

        $currentStatus = (string) ($replyEvent->get('triageStatus') ?: '');
        if ($currentStatus === '') {
            throw new BadRequest(
                'ReplyEvent has no triage lifecycle; only actionable events initialized at ingress can be triaged.'
            );
        }

        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("ReplyEvent triage transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        $reason = $options['reason'] ?? null;
        if ($targetStatus === self::TRIAGE_CLOSED && (!is_string($reason) || trim($reason) === '')) {
            throw new BadRequest('ReplyEvent close requires a closedReason.');
        }

        $action = $this->resolveAction($currentStatus, $targetStatus);
        if (($options['skipAuthorization'] ?? false) !== true) {
            $this->authorize($replyEvent, $action);
        }

        $now = $this->resolveNow($options);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($replyEvent, $currentStatus, $targetStatus, $action, $reason, $now): Entity {
                if ($targetStatus === self::TRIAGE_CLOSED) {
                    $replyEvent->set('closedReason', trim((string) $reason));
                    $replyEvent->set('closedAt', $now->format('Y-m-d H:i:s'));
                    $replyEvent->set('closedById', $this->user->getId());
                }

                if ($targetStatus === self::TRIAGE_IN_PROGRESS) {
                    // assign: the triaging operator takes ownership.
                    $replyEvent->set('assignedUserId', $this->user->getId());
                }

                if ($targetStatus === self::TRIAGE_OPEN) {
                    // release: unassign back to the open queue.
                    $replyEvent->set('assignedUserId', null);
                }

                $replyEvent->set('triageStatus', $targetStatus);
                $this->entityManager->saveEntity($replyEvent, [
                    StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED => true,
                ]);
                $this->afterTriage($replyEvent, $currentStatus, $targetStatus, $action, $reason);

                return $replyEvent;
            }
        );
    }

    /**
     * Extension hook for future side effects (notifications, queue fan-out).
     * Audit fields for CLOSED are applied before save in transition().
     */
    protected function afterTriage(Entity $replyEvent, string $fromStatus, string $toStatus, string $action, ?string $reason): void
    {
    }

    /**
     * @param array{now?: DateTimeImmutable|string} $options
     */
    private function resolveNow(array $options): DateTimeImmutable
    {
        $now = $options['now'] ?? new DateTimeImmutable();
        if (is_string($now)) {
            $now = new DateTimeImmutable($now);
        }
        if (!$now instanceof DateTimeImmutable) {
            throw new BadRequest('Invalid ReplyEvent triage clock.');
        }

        return $now;
    }

    private function assertKnownStatus(string $status): void
    {
        if (!array_key_exists($status, self::VALID_TRANSITIONS)) {
            throw new BadRequest("Unknown ReplyEvent triage status: {$status}.");
        }
    }
}
