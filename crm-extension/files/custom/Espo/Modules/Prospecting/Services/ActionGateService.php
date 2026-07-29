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
 * Human authorization boundary for proposed C22 execution actions.
 *
 * This service grants permission only. It does not execute providers, send
 * messages, mutate CRM lifecycle state, or schedule autonomous work.
 */
final class ActionGateService
{
    public const ENTITY_TYPE = 'ActionGate';

    public const DECISION_PENDING = 'PENDING';
    public const DECISION_APPROVED = 'APPROVED';
    public const DECISION_DENIED = 'DENIED';
    public const DECISION_DEFERRED = 'DEFERRED';

    /** @var list<string> */
    private const FINAL_DECISIONS = [
        self::DECISION_APPROVED,
        self::DECISION_DENIED,
        self::DECISION_DEFERRED,
    ];

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'prospectCandidateId',
        'prospectRunId',
        'actionType',
        'actionReference',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {
    }

    /**
     * @param array<string, mixed> $attributes
     */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest('ActionGate create contains unsupported fields.');
        }

        $candidate = $this->existingEntity(
            'ProspectCandidate',
            $this->requiredString($attributes, 'prospectCandidateId')
        );
        $run = $this->existingEntity(
            'ProspectRun',
            $this->requiredString($attributes, 'prospectRunId')
        );
        if ((string) $candidate->get('prospectRunId') !== $run->getId()) {
            throw new BadRequest(
                'ActionGate candidate must belong to its ProspectRun.'
            );
        }

        $actorId = $this->authenticatedActorId();
        $actionType = $this->requiredString($attributes, 'actionType');
        if (!preg_match('/^[A-Z][A-Z0-9_]{0,99}$/', $actionType)) {
            throw new BadRequest(
                'ActionGate actionType must be an uppercase action identifier.'
            );
        }

        $gate = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $gate->set([
            'name' => 'Action Gate: ' . $actionType,
            'prospectCandidateId' => $candidate->getId(),
            'prospectRunId' => $run->getId(),
            'actionType' => $actionType,
            'actionReference' => $this->optionalString(
                $attributes['actionReference'] ?? null
            ),
            'decision' => self::DECISION_PENDING,
            'requestedById' => $actorId,
        ]);
        $this->entityManager->saveEntity($gate, [
            C22ExecutionSaveOption::ACTION_GATE_CREATE_AUTHORIZED => true,
        ]);

        return $gate;
    }

    public function decide(
        Entity $gate,
        string $decision,
        ?string $reason = null
    ): Entity {
        $this->assertGate($gate);
        if (!$this->acl->checkEntityEdit($gate)) {
            throw new Forbidden();
        }
        if (!in_array($decision, self::FINAL_DECISIONS, true)) {
            throw new BadRequest('ActionGate decision is unsupported.');
        }
        if ((string) $gate->get('decision') !== self::DECISION_PENDING) {
            throw new Conflict('Only a PENDING ActionGate can be decided.');
        }

        $normalizedReason = $this->optionalString($reason);
        if ($decision === self::DECISION_DENIED && $normalizedReason === null) {
            throw new BadRequest('A DENIED ActionGate requires a reason.');
        }

        $gate->set([
            'decision' => $decision,
            'decidedById' => $this->authenticatedActorId(),
            'decidedAt' => date('Y-m-d H:i:s'),
            'reason' => $normalizedReason,
        ]);
        $this->entityManager->saveEntity($gate, [
            C22ExecutionSaveOption::ACTION_GATE_DECISION_AUTHORIZED => true,
        ]);

        return $gate;
    }

    public function assertApprovedForExecution(Entity $gate): void
    {
        $this->assertGate($gate);
        if ((string) $gate->get('decision') !== self::DECISION_APPROVED) {
            throw new Forbidden(
                'No C22 execution is permitted without an APPROVED ActionGate.'
            );
        }
    }

    private function assertGate(Entity $gate): void
    {
        if ($gate->getEntityType() !== self::ENTITY_TYPE || $gate->isNew()) {
            throw new BadRequest('ActionGate must be an existing gate record.');
        }
    }

    private function existingEntity(string $entityType, string $id): Entity
    {
        $entity = $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            throw new BadRequest("ActionGate requires existing {$entityType}.");
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
            throw new BadRequest("ActionGate requires {$field}.");
        }

        return $value;
    }

    private function authenticatedActorId(): string
    {
        $actorId = $this->optionalString($this->user->getId());
        if ($actorId === null) {
            throw new Forbidden('ActionGate requires an authenticated actor.');
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
