<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * C14.3.1C CRM terminal-result writer.
 *
 * It updates SendExecution only. Saving that source entity invokes the
 * existing projection hook; this service never creates events or writes Lead.
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

    public function __construct(private EntityManager $entityManager) {}

    public function apply(SendExecutionBridgeResult $result): string
    {
        $execution = $this->entityManager->getEntityById('SendExecution', $result->executionId());
        if (!$execution instanceof Entity) {
            return 'SEND_EXECUTION_NOT_FOUND';
        }

        $currentStatus = (string) $execution->get('status');
        if ($currentStatus === 'READY') {
            $this->applyReadyTransition($execution, $result);
            $this->entityManager->saveEntity($execution);

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
                'status' => 'SENT',
                'providerMessageId' => $result->providerAttemptId(),
                'failureCategory' => null,
                'lastError' => null,
            ]);

            return;
        }

        $execution->set([
            'status' => 'FAILED',
            'providerMessageId' => null,
            'failureCategory' => $this->failureCategory($result->errorClass()),
            'lastError' => $result->errorCode(),
        ]);
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
