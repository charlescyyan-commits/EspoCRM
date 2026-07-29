<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Modules\Prospecting\Execution\ExecutionAction;
use Espo\Modules\Prospecting\ProviderBoundary\ConnectorBoundary;
use Espo\Modules\Prospecting\ProviderBoundary\ProviderResultEnvelope;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use RuntimeException;
use Throwable;

/**
 * Synchronous governance orchestration across WP1 and WP2 boundaries.
 *
 * It invokes only the ConnectorBoundary interface and contains no concrete
 * external-service or CRM lifecycle behavior.
 */
final class ExecutionOrchestrationService
{
    /** @var list<string> */
    private const FAILURE_CATEGORIES = [
        'TRANSIENT',
        'PERMANENT',
        'GOVERNANCE',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private ActionGateService $actionGateService,
        private ExecutionLedgerService $executionLedgerService,
        private ProspectRunLifecycleService $prospectRunLifecycleService,
        private ConnectorBoundary $connectorBoundary,
    ) {
    }

    public function requestAction(ExecutionAction $action): Entity
    {
        [$candidate, $run] = $this->executionContext($action);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($action, $candidate, $run): Entity {
                $status = (string) (
                    $run->get('status')
                    ?: ProspectRunLifecycleService::STATUS_CREATED
                );
                if (
                    !in_array(
                        $status,
                        [
                            ProspectRunLifecycleService::STATUS_CREATED,
                            ProspectRunLifecycleService::STATUS_PLANNING,
                            ProspectRunLifecycleService::STATUS_WAITING_APPROVAL,
                        ],
                        true
                    )
                ) {
                    throw new BadRequest(
                        'ProspectRun cannot accept a new execution action.'
                    );
                }
                if ($status === ProspectRunLifecycleService::STATUS_CREATED) {
                    $this->prospectRunLifecycleService->transition(
                        $run,
                        ProspectRunLifecycleService::STATUS_PLANNING
                    );
                }

                $gate = $this->actionGateService->create([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionType' => $action->providerType(),
                    'actionReference' => $action->actionId(),
                ]);
                $this->executionLedgerService->append([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionGateId' => $gate->getId(),
                    'eventType' =>
                        ExecutionLedgerService::EVENT_ACTION_REQUESTED,
                    'outcome' => 'PENDING',
                ]);

                if (
                    (string) $run->get('status')
                    === ProspectRunLifecycleService::STATUS_PLANNING
                ) {
                    $this->prospectRunLifecycleService->transition(
                        $run,
                        ProspectRunLifecycleService::STATUS_WAITING_APPROVAL
                    );
                }

                return $gate;
            }
        );
    }

    public function decideAction(
        ExecutionAction $action,
        Entity $gate,
        string $decision,
        ?string $reason = null
    ): Entity {
        [$candidate, $run] = $this->executionContext($action);
        $this->assertGateContext($action, $gate, $candidate, $run);

        return $this->entityManager->getTransactionManager()->run(
            function () use (
                $action,
                $candidate,
                $run,
                $gate,
                $decision,
                $reason
            ): Entity {
                $decidedGate = $this->actionGateService->decide(
                    $gate,
                    $decision,
                    $reason
                );
                $eventType = $decision === ActionGateService::DECISION_APPROVED
                    ? ExecutionLedgerService::EVENT_APPROVAL_GRANTED
                    : ExecutionLedgerService::EVENT_GATE_DECISION;
                $this->executionLedgerService->append([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionGateId' => $decidedGate->getId(),
                    'eventType' => $eventType,
                    'outcome' => $decision,
                ]);

                return $decidedGate;
            }
        );
    }

    public function execute(
        ExecutionAction $action,
        Entity $gate
    ): ProviderResultEnvelope {
        [$candidate, $run] = $this->executionContext($action);
        $this->assertGateContext($action, $gate, $candidate, $run);
        $this->actionGateService->assertApprovedForExecution($gate);

        $this->entityManager->getTransactionManager()->run(
            function () use ($candidate, $run, $gate): void {
                $this->prospectRunLifecycleService->transition(
                    $run,
                    ProspectRunLifecycleService::STATUS_EXECUTING,
                    $gate
                );
                $this->executionLedgerService->append([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionGateId' => $gate->getId(),
                    'eventType' =>
                        ExecutionLedgerService::EVENT_EXECUTION_STARTED,
                ]);
            }
        );

        try {
            $result = $this->connectorBoundary->execute($action->request());
            $this->assertMatchingResult($action, $result);
        } catch (Throwable) {
            $this->recordFailure(
                $candidate,
                $run,
                $gate,
                'GOVERNANCE'
            );
            throw new RuntimeException(
                'Connector boundary execution failed.'
            );
        }

        if ($result->status() === ProviderResultEnvelope::SUCCEEDED) {
            $this->recordCompletion($candidate, $run, $gate);
        } elseif (
            in_array(
                $result->status(),
                [
                    ProviderResultEnvelope::FAILED,
                    ProviderResultEnvelope::REJECTED,
                ],
                true
            )
        ) {
            $this->recordFailure(
                $candidate,
                $run,
                $gate,
                $this->failureCategory($result)
            );
        }

        return $result;
    }

    /**
     * @return array{0: Entity, 1: Entity}
     */
    private function executionContext(ExecutionAction $action): array
    {
        $candidate = $this->existingEntity(
            'ProspectCandidate',
            $action->prospectCandidateId()
        );
        $run = $this->existingEntity(
            ProspectRunLifecycleService::ENTITY_TYPE,
            $action->prospectRunId()
        );
        if ((string) $candidate->get('prospectRunId') !== $run->getId()) {
            throw new BadRequest(
                'ExecutionAction candidate must belong to its ProspectRun.'
            );
        }

        return [$candidate, $run];
    }

    private function assertGateContext(
        ExecutionAction $action,
        Entity $gate,
        Entity $candidate,
        Entity $run
    ): void {
        if (
            $gate->getEntityType() !== ActionGateService::ENTITY_TYPE
            || $gate->isNew()
            || (string) $gate->get('prospectCandidateId')
                !== $candidate->getId()
            || (string) $gate->get('prospectRunId') !== $run->getId()
            || (string) $gate->get('actionType')
                !== $action->providerType()
            || (string) $gate->get('actionReference')
                !== $action->actionId()
        ) {
            throw new BadRequest(
                'ActionGate does not authorize this ExecutionAction.'
            );
        }
    }

    private function assertMatchingResult(
        ExecutionAction $action,
        ProviderResultEnvelope $result
    ): void {
        if (
            $result->requestId() !== $action->request()->requestId()
            || $result->providerType() !== $action->providerType()
        ) {
            throw new BadRequest(
                'Provider result does not match the execution action.'
            );
        }
    }

    private function recordCompletion(
        Entity $candidate,
        Entity $run,
        Entity $gate
    ): void {
        $this->entityManager->getTransactionManager()->run(
            function () use ($candidate, $run, $gate): void {
                $this->executionLedgerService->append([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionGateId' => $gate->getId(),
                    'eventType' =>
                        ExecutionLedgerService::EVENT_EXECUTION_COMPLETED,
                    'outcome' => 'SUCCEEDED',
                ]);
                $this->prospectRunLifecycleService->transition(
                    $run,
                    ProspectRunLifecycleService::STATUS_COMPLETED
                );
            }
        );
    }

    private function recordFailure(
        Entity $candidate,
        Entity $run,
        Entity $gate,
        string $failureCategory
    ): void {
        $this->entityManager->getTransactionManager()->run(
            function () use (
                $candidate,
                $run,
                $gate,
                $failureCategory
            ): void {
                $this->executionLedgerService->append([
                    'prospectCandidateId' => $candidate->getId(),
                    'prospectRunId' => $run->getId(),
                    'actionGateId' => $gate->getId(),
                    'eventType' =>
                        ExecutionLedgerService::EVENT_EXECUTION_FAILED,
                    'outcome' => 'FAILED',
                    'failureCategory' => $failureCategory,
                ]);
                $this->prospectRunLifecycleService->transition(
                    $run,
                    ProspectRunLifecycleService::STATUS_FAILED
                );
            }
        );
    }

    private function failureCategory(
        ProviderResultEnvelope $result
    ): string {
        $failureCategory = (string) $result->failureCategory();
        if (!in_array($failureCategory, self::FAILURE_CATEGORIES, true)) {
            return 'GOVERNANCE';
        }

        return $failureCategory;
    }

    private function existingEntity(string $entityType, string $id): Entity
    {
        $entity = $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            throw new BadRequest(
                "Execution orchestration requires existing {$entityType}."
            );
        }
        if (!$this->acl->checkEntityRead($entity)) {
            throw new Forbidden();
        }

        return $entity;
    }
}
