<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Appends metadata-only C22 authorization and execution evidence.
 *
 * The service performs no provider call, message delivery, lifecycle mutation,
 * retry scheduling, or autonomous execution.
 */
final class ExecutionLedgerService
{
    public const ENTITY_TYPE = 'ExecutionLedger';

    public const EVENT_ACTION_REQUEST = 'ACTION_REQUEST';
    public const EVENT_GATE_DECISION = 'GATE_DECISION';
    public const EVENT_EXECUTION_STARTED = 'EXECUTION_STARTED';
    public const EVENT_EXECUTION_RESULT = 'EXECUTION_RESULT';
    public const EVENT_FAILURE_CLASSIFICATION = 'FAILURE_CLASSIFICATION';

    /** @var list<string> */
    private const EVENT_TYPES = [
        self::EVENT_ACTION_REQUEST,
        self::EVENT_GATE_DECISION,
        self::EVENT_EXECUTION_STARTED,
        self::EVENT_EXECUTION_RESULT,
        self::EVENT_FAILURE_CLASSIFICATION,
    ];

    /** @var list<string> */
    private const OUTCOMES = [
        'PENDING',
        'APPROVED',
        'DENIED',
        'DEFERRED',
        'SUCCEEDED',
        'FAILED',
    ];

    /** @var list<string> */
    private const FAILURE_CATEGORIES = [
        'TRANSIENT',
        'PERMANENT',
        'GOVERNANCE',
    ];

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'prospectCandidateId',
        'prospectRunId',
        'actionGateId',
        'eventType',
        'outcome',
        'failureCategory',
        'supersedesId',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private ActionGateService $actionGateService,
    ) {
    }

    /**
     * @param array<string, mixed> $attributes
     */
    public function append(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest(
                'ExecutionLedger append contains unsupported fields.'
            );
        }

        $candidate = $this->existingEntity(
            'ProspectCandidate',
            $this->requiredString($attributes, 'prospectCandidateId')
        );
        $run = $this->existingEntity(
            'ProspectRun',
            $this->requiredString($attributes, 'prospectRunId')
        );
        $gate = $this->existingEntity(
            ActionGateService::ENTITY_TYPE,
            $this->requiredString($attributes, 'actionGateId')
        );
        $this->assertSameExecutionContext($candidate, $run, $gate);

        $eventType = $this->requiredEnum(
            $attributes,
            'eventType',
            self::EVENT_TYPES
        );
        $outcome = $this->optionalEnum(
            $attributes['outcome'] ?? null,
            self::OUTCOMES,
            'outcome'
        );
        $failureCategory = $this->optionalEnum(
            $attributes['failureCategory'] ?? null,
            self::FAILURE_CATEGORIES,
            'failureCategory'
        );
        $this->assertEventSemantics(
            $eventType,
            $outcome,
            $failureCategory,
            $gate
        );

        $supersedesId = $this->optionalString(
            $attributes['supersedesId'] ?? null
        );
        if ($supersedesId !== null) {
            $this->assertSupersession(
                $supersedesId,
                (string) $candidate->getId(),
                (string) $run->getId(),
                (string) $gate->getId()
            );
        }

        $ledger = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $ledger->set([
            'name' => 'C22 Ledger: ' . $eventType,
            'prospectCandidateId' => $candidate->getId(),
            'prospectRunId' => $run->getId(),
            'actionGateId' => $gate->getId(),
            'eventType' => $eventType,
            'outcome' => $outcome,
            'failureCategory' => $failureCategory,
            'actorId' => $this->authenticatedActorId(),
            'occurredAt' => date('Y-m-d H:i:s'),
            'supersedesId' => $supersedesId,
        ]);
        $this->entityManager->saveEntity($ledger, [
            C22ExecutionSaveOption::EXECUTION_LEDGER_CREATE_AUTHORIZED => true,
        ]);

        return $ledger;
    }

    private function assertEventSemantics(
        string $eventType,
        ?string $outcome,
        ?string $failureCategory,
        Entity $gate
    ): void {
        if (
            in_array(
                $eventType,
                [self::EVENT_EXECUTION_STARTED, self::EVENT_EXECUTION_RESULT],
                true
            )
        ) {
            $this->actionGateService->assertApprovedForExecution($gate);
        }

        if (
            $eventType === self::EVENT_GATE_DECISION
            && $outcome !== (string) $gate->get('decision')
        ) {
            throw new BadRequest(
                'ExecutionLedger gate decision must match ActionGate.'
            );
        }
        if (
            $eventType === self::EVENT_EXECUTION_RESULT
            && !in_array($outcome, ['SUCCEEDED', 'FAILED'], true)
        ) {
            throw new BadRequest(
                'ExecutionLedger execution result requires SUCCEEDED or FAILED.'
            );
        }
        if (
            $eventType === self::EVENT_FAILURE_CLASSIFICATION
            && ($outcome !== 'FAILED' || $failureCategory === null)
        ) {
            throw new BadRequest(
                'ExecutionLedger failure classification requires FAILED and a category.'
            );
        }
        if ($outcome === 'FAILED' && $failureCategory === null) {
            throw new BadRequest(
                'ExecutionLedger FAILED outcome requires failureCategory.'
            );
        }
        if ($outcome !== 'FAILED' && $failureCategory !== null) {
            throw new BadRequest(
                'ExecutionLedger failureCategory requires FAILED outcome.'
            );
        }
    }

    private function assertSameExecutionContext(
        Entity $candidate,
        Entity $run,
        Entity $gate
    ): void {
        if (
            (string) $candidate->get('prospectRunId') !== (string) $run->getId()
            || (string) $gate->get('prospectCandidateId')
                !== (string) $candidate->getId()
            || (string) $gate->get('prospectRunId') !== (string) $run->getId()
        ) {
            throw new BadRequest(
                'ExecutionLedger references must share one C22 execution context.'
            );
        }
    }

    private function assertSupersession(
        string $predecessorId,
        string $candidateId,
        string $runId,
        string $gateId
    ): void {
        $predecessor = $this->existingEntity(
            self::ENTITY_TYPE,
            $predecessorId
        );
        if (
            (string) $predecessor->get('prospectCandidateId') !== $candidateId
            || (string) $predecessor->get('prospectRunId') !== $runId
            || (string) $predecessor->get('actionGateId') !== $gateId
        ) {
            throw new BadRequest(
                'ExecutionLedger supersession must retain execution context.'
            );
        }

        $successor = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['supersedesId' => $predecessorId])
            ->findOne();
        if ($successor) {
            throw new Conflict(
                'ExecutionLedger already has a direct successor.'
            );
        }
    }

    private function existingEntity(string $entityType, string $id): Entity
    {
        $entity = $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            throw new BadRequest(
                "ExecutionLedger requires existing {$entityType}."
            );
        }
        if (!$this->acl->checkEntityRead($entity)) {
            throw new Forbidden();
        }

        return $entity;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredString(array $attributes, string $field): string
    {
        $value = $this->optionalString($attributes[$field] ?? null);
        if ($value === null) {
            throw new BadRequest("ExecutionLedger requires {$field}.");
        }

        return $value;
    }

    /**
     * @param array<string, mixed> $attributes
     * @param list<string> $allowed
     */
    private function requiredEnum(
        array $attributes,
        string $field,
        array $allowed
    ): string {
        $value = $this->optionalEnum(
            $attributes[$field] ?? null,
            $allowed,
            $field
        );
        if ($value === null) {
            throw new BadRequest("ExecutionLedger requires {$field}.");
        }

        return $value;
    }

    /** @param list<string> $allowed */
    private function optionalEnum(
        mixed $value,
        array $allowed,
        string $field
    ): ?string {
        $value = $this->optionalString($value);
        if ($value !== null && !in_array($value, $allowed, true)) {
            throw new BadRequest("ExecutionLedger {$field} is unsupported.");
        }

        return $value;
    }

    private function authenticatedActorId(): string
    {
        $actorId = $this->optionalString($this->user->getId());
        if ($actorId === null) {
            throw new Forbidden(
                'ExecutionLedger requires an authenticated actor.'
            );
        }

        return $actorId;
    }

    private function optionalString(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
