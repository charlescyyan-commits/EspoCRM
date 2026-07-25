<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * C14.3.1C CRM terminal-result writer.
 *
 * Updates SendExecution provider-trace fields and delegates status mutation to
 * SendExecutionTransitionService. Never creates events or writes Lead.
 */
final class SendExecutionResultAdapterService
{
    private const ERROR_CLASS_TO_FAILURE_CATEGORY = [
        BridgeErrorClass::NETWORK => 'NETWORK',
        BridgeErrorClass::AUTH => 'AUTH',
        BridgeErrorClass::VALIDATION => 'VALIDATION',
        BridgeErrorClass::PROVIDER => 'PROVIDER',
        BridgeErrorClass::UNKNOWN => 'UNKNOWN',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private SendExecutionTransitionService $transitionService,
    ) {}

    public function apply(SendExecutionBridgeResult $result): string
    {
        $execution = $this->entityManager->getEntityById('SendExecution', $result->executionId());
        if (!$execution instanceof Entity) {
            return 'SEND_EXECUTION_NOT_FOUND';
        }

        $currentStatus = (string) $execution->get('status');
        if ($currentStatus === 'READY') {
            $this->applyReadyTransition($execution, $result);

            return 'APPLIED';
        }
        if ($this->isDuplicate($execution, $result)) {
            return 'DUPLICATE_RESULT';
        }
        if (in_array($currentStatus, ['SENT', 'FAILED'], true)) {
            return 'RESULT_CONFLICT';
        }

        return 'RESULT_NOT_APPLICABLE';
    }

    private function applyReadyTransition(Entity $execution, SendExecutionBridgeResult $result): void
    {
        if ($result->normalizedStatus() === BridgeNormalizedStatus::SENT) {
            $execution->set([
                'providerMessageId' => $result->providerAttemptId(),
                'failureCategory' => null,
                'lastError' => null,
            ]);
            $this->transitionTo($execution, SendExecutionTransitionService::STATUS_SENT);

            return;
        }

        $execution->set([
            'providerMessageId' => null,
            'failureCategory' => $this->failureCategory($result->errorClass()),
            'lastError' => $result->errorCode(),
        ]);
        $this->transitionTo($execution, SendExecutionTransitionService::STATUS_FAILED);
    }

    private function transitionTo(Entity $execution, string $targetStatus): void
    {
        try {
            $this->transitionService->transition($execution, $targetStatus, [
                'skipAuthorization' => true,
            ]);
        } catch (BadRequest $exception) {
            throw new BridgeRejectionException($exception->getMessage(), 0, $exception);
        }
    }

    private function isDuplicate(Entity $execution, SendExecutionBridgeResult $result): bool
    {
        if ($result->normalizedStatus() === BridgeNormalizedStatus::SENT) {
            return $execution->get('status') === 'SENT'
                && $execution->get('providerMessageId') === $result->providerAttemptId();
        }

        return $execution->get('status') === 'FAILED'
            && $execution->get('failureCategory') === $this->failureCategory($result->errorClass())
            && $execution->get('lastError') === $result->errorCode();
    }

    private function failureCategory(?string $errorClass): string
    {
        $category = self::ERROR_CLASS_TO_FAILURE_CATEGORY[$errorClass ?? ''] ?? null;
        if ($category === null) {
            throw new BridgeRejectionException('Unknown error class.');
        }

        return $category;
    }
}
