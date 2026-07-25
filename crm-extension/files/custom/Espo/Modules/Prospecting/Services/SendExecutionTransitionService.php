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
 * Sole intended writer of SendExecution.status (ADR-C18 / adr-c18-sendexecution-v1).
 *
 * Adapters are not migrated in WP1.1; they must later call this service for any
 * status transition. Provider-trace field writes remain adapter-owned until that
 * migration lands.
 */
class SendExecutionTransitionService
{
    public const STATUS_CREATED = 'CREATED';
    public const STATUS_READY = 'READY';
    public const STATUS_SENT = 'SENT';
    public const STATUS_FAILED = 'FAILED';
    public const STATUS_CANCELLED = 'CANCELLED';

    public const ACTION_PREPARE = 'sendExecution.prepare';
    public const ACTION_RECORD_SENT = 'sendExecution.recordSent';
    public const ACTION_RECORD_FAILED = 'sendExecution.recordFailed';
    public const ACTION_RETRY = 'sendExecution.retry';
    public const ACTION_CANCEL = 'sendExecution.cancel';

    public const GOVERNANCE_MARKER = 'adr-c18-sendexecution-v1';

    /** @var array<string, list<string>> */
    private const VALID_TRANSITIONS = [
        self::STATUS_CREATED => [self::STATUS_READY],
        self::STATUS_READY => [self::STATUS_SENT, self::STATUS_FAILED, self::STATUS_CANCELLED],
        self::STATUS_FAILED => [self::STATUS_READY, self::STATUS_CANCELLED],
        self::STATUS_SENT => [],
        self::STATUS_CANCELLED => [],
    ];

    /** @var array<string, array<string, string>> */
    private const TRANSITION_ACTIONS = [
        self::STATUS_CREATED => [
            self::STATUS_READY => self::ACTION_PREPARE,
        ],
        self::STATUS_READY => [
            self::STATUS_SENT => self::ACTION_RECORD_SENT,
            self::STATUS_FAILED => self::ACTION_RECORD_FAILED,
            self::STATUS_CANCELLED => self::ACTION_CANCEL,
        ],
        self::STATUS_FAILED => [
            self::STATUS_READY => self::ACTION_RETRY,
            self::STATUS_CANCELLED => self::ACTION_CANCEL,
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
     * Resolves the ADR action key required for a status edge.
     */
    public function resolveAction(string $currentStatus, string $targetStatus): string
    {
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("SendExecution transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        $action = self::TRANSITION_ACTIONS[$currentStatus][$targetStatus] ?? null;
        if (!is_string($action) || $action === '') {
            throw new BadRequest("SendExecution transition {$currentStatus} -> {$targetStatus} has no authorization action.");
        }

        return $action;
    }

    /**
     * Authorizes a workflow action for the current user against the execution record.
     */
    public function authorize(Entity $execution, string $action): void
    {
        if ($execution->getEntityType() !== 'SendExecution') {
            throw new BadRequest('SendExecution transition requires a SendExecution entity.');
        }

        if (!$this->acl->checkEntityEdit($execution)) {
            throw new Forbidden();
        }

        $knownActions = [
            self::ACTION_PREPARE,
            self::ACTION_RECORD_SENT,
            self::ACTION_RECORD_FAILED,
            self::ACTION_RETRY,
            self::ACTION_CANCEL,
        ];
        if (!in_array($action, $knownActions, true)) {
            throw new BadRequest('Unsupported SendExecution workflow action.');
        }

        // WP1.1 foundation: edit ACL + known action key. Role bindings land with
        // metadata policy under GOVERNANCE_MARKER in a later WP.
        if ($this->user->isAdmin()) {
            return;
        }
    }

    /**
     * @param array{now?: DateTimeImmutable|string, skipAuthorization?: bool} $options
     */
    public function transition(Entity $execution, string $targetStatus, array $options = []): Entity
    {
        if ($execution->getEntityType() !== 'SendExecution') {
            throw new BadRequest('SendExecution transition requires a SendExecution entity.');
        }

        $currentStatus = (string) ($execution->get('status') ?: self::STATUS_CREATED);
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("SendExecution transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        if (($options['skipAuthorization'] ?? false) !== true) {
            $this->authorize($execution, $this->resolveAction($currentStatus, $targetStatus));
        }

        if ($currentStatus === self::STATUS_FAILED && $targetStatus === self::STATUS_READY) {
            $this->assertRetryAllowed($execution);
        }

        $now = $this->resolveNow($options);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($execution, $currentStatus, $targetStatus, $now): Entity {
                if ($targetStatus === self::STATUS_SENT) {
                    $execution->set('sentAt', $now->format('Y-m-d H:i:s'));
                }

                $execution->set('status', $targetStatus);
                $this->entityManager->saveEntity($execution, [
                    StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED => true,
                ]);
                $this->afterTransition($execution, $currentStatus, $targetStatus);

                return $execution;
            }
        );
    }

    /**
     * Extension hook for future side effects (notifications, queue fan-out).
     * Audit timestamp for SENT is applied before save in transition().
     */
    protected function afterTransition(Entity $execution, string $fromStatus, string $toStatus): void
    {
    }

    private function assertRetryAllowed(Entity $execution): void
    {
        $retryCount = (int) ($execution->get('retryCount') ?? 0);
        $maxRetries = (int) ($execution->get('maxRetries') ?? 0);
        if ($retryCount >= $maxRetries) {
            throw new BadRequest('SendExecution retry limit reached for maxRetries.');
        }
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
            throw new BadRequest('Invalid SendExecution transition clock.');
        }

        return $now;
    }

    private function assertKnownStatus(string $status): void
    {
        if (!array_key_exists($status, self::VALID_TRANSITIONS)) {
            throw new BadRequest("Unknown SendExecution status: {$status}.");
        }
    }
}
