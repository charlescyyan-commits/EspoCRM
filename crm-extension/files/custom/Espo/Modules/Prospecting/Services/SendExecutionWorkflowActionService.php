<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\NotFound;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Command adapter for C19 WP2 recovery actions.
 *
 * This class authorizes an operator command and delegates the existing state
 * edge to SendExecutionTransitionService. It owns neither a state machine nor
 * persistence of SendExecution.status.
 */
class SendExecutionWorkflowActionService
{
    private const IGNORE_REASON = 'IGNORED';

    /** @var list<string> */
    private const CANCEL_REASONS = [
        self::IGNORE_REASON,
        'ABANDONED',
        'DUPLICATE',
        'OTHER',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private User $user,
        private WorkflowAuthorizationService $authorizationService,
        private SendExecutionTransitionService $transitionService,
    ) {}

    /**
     * @return array{success: true, id: string, status: string, retryCount: int, cancelledAt: string|null}
     */
    public function execute(string $executionId, string $action, ?string $reason = null): array
    {
        $execution = $this->entityManager->getEntityById('SendExecution', $executionId);
        if (!$execution instanceof Entity) {
            throw new NotFound('SendExecution was not found.');
        }

        $authorizedAction = $this->authorizationService->authorizeSendExecutionAction(
            $execution,
            $this->user,
            $action,
        );

        if ($authorizedAction === WorkflowAuthorizationService::ACTION_SEND_EXECUTION_RETRY) {
            $execution = $this->transitionService->transition(
                $execution,
                SendExecutionTransitionService::STATUS_READY,
                [
                    'workflowAuthorizationChecked' => true,
                    'reason' => $this->normalizeOptionalReason($reason),
                ],
            );

            return $this->buildResult($execution);
        }

        if ($authorizedAction !== WorkflowAuthorizationService::ACTION_SEND_EXECUTION_CANCEL) {
            throw new BadRequest('Unsupported SendExecution workflow action.');
        }

        $cancelReason = $action === 'ignore'
            ? self::IGNORE_REASON
            : $this->normalizeCancelReason($reason);

        $execution = $this->transitionService->transition(
            $execution,
            SendExecutionTransitionService::STATUS_CANCELLED,
            [
                'workflowAuthorizationChecked' => true,
                'reason' => $cancelReason,
            ],
        );

        return $this->buildResult($execution);
    }

    private function normalizeOptionalReason(?string $reason): ?string
    {
        $reason = trim((string) $reason);

        return $reason !== '' ? $reason : null;
    }

    private function normalizeCancelReason(?string $reason): string
    {
        $reason = strtoupper(trim((string) $reason));
        if (!in_array($reason, self::CANCEL_REASONS, true)) {
            throw new BadRequest('SendExecution cancel requires a valid cancelReason.');
        }

        return $reason;
    }

    /** @return array{success: true, id: string, status: string, retryCount: int, cancelledAt: string|null} */
    private function buildResult(Entity $execution): array
    {
        return [
            'success' => true,
            'id' => (string) $execution->getId(),
            'status' => (string) $execution->get('status'),
            'retryCount' => (int) ($execution->get('retryCount') ?? 0),
            'cancelledAt' => $execution->get('cancelledAt') ?: null,
        ];
    }
}
