<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Controlled lifecycle transitions for the C22 ProspectRun container.
 */
final class ProspectRunLifecycleService
{
    public const ENTITY_TYPE = 'ProspectRun';

    public const STATUS_CREATED = 'CREATED';
    public const STATUS_PLANNING = 'PLANNING';
    public const STATUS_WAITING_APPROVAL = 'WAITING_APPROVAL';
    public const STATUS_EXECUTING = 'EXECUTING';
    public const STATUS_COMPLETED = 'COMPLETED';
    public const STATUS_FAILED = 'FAILED';
    public const STATUS_CANCELLED = 'CANCELLED';

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        self::STATUS_CREATED => [
            self::STATUS_PLANNING,
            self::STATUS_CANCELLED,
        ],
        self::STATUS_PLANNING => [
            self::STATUS_WAITING_APPROVAL,
            self::STATUS_FAILED,
            self::STATUS_CANCELLED,
        ],
        self::STATUS_WAITING_APPROVAL => [
            self::STATUS_EXECUTING,
            self::STATUS_FAILED,
            self::STATUS_CANCELLED,
        ],
        self::STATUS_EXECUTING => [
            self::STATUS_COMPLETED,
            self::STATUS_FAILED,
            self::STATUS_CANCELLED,
        ],
        self::STATUS_COMPLETED => [],
        self::STATUS_FAILED => [],
        self::STATUS_CANCELLED => [],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private ActionGateService $actionGateService,
    ) {
    }

    public function transition(
        Entity $run,
        string $targetStatus,
        ?Entity $gate = null
    ): Entity {
        $this->assertRun($run);
        if (!$this->acl->checkEntityEdit($run)) {
            throw new Forbidden();
        }
        if (!array_key_exists($targetStatus, self::TRANSITIONS)) {
            throw new BadRequest('ProspectRun target status is unsupported.');
        }

        $currentStatus = (string) (
            $run->get('status') ?: self::STATUS_CREATED
        );
        if (
            !array_key_exists($currentStatus, self::TRANSITIONS)
            || !in_array(
                $targetStatus,
                self::TRANSITIONS[$currentStatus],
                true
            )
        ) {
            throw new BadRequest(
                "ProspectRun transition {$currentStatus} -> {$targetStatus} is not allowed."
            );
        }

        if ($targetStatus === self::STATUS_EXECUTING) {
            if (!$gate instanceof Entity) {
                throw new Forbidden(
                    'ProspectRun execution requires an ActionGate.'
                );
            }
            $this->actionGateService->assertApprovedForExecution($gate);
            if ((string) $gate->get('prospectRunId') !== $run->getId()) {
                throw new BadRequest(
                    'Approved ActionGate must belong to the ProspectRun.'
                );
            }
        }

        $run->set('status', $targetStatus);
        $this->entityManager->saveEntity($run, [
            C22ExecutionSaveOption::PROSPECT_RUN_STATUS_MUTATION_AUTHORIZED =>
                true,
        ]);

        return $run;
    }

    private function assertRun(Entity $run): void
    {
        if (
            $run->getEntityType() !== self::ENTITY_TYPE
            || $run->isNew()
        ) {
            throw new BadRequest(
                'ProspectRun lifecycle requires an existing ProspectRun.'
            );
        }
    }
}
