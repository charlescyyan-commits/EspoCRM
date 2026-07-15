<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Records a terminal connector bridge result in CRM source records.
 *
 * This adapter writes only SendExecution and an optional SENT EmailEvent. The
 * existing after-save hooks own all Lead lifecycle projection.
 */
final class SendExecutionBridgeAdapterService
{
    private const ERROR_CLASS_TO_FAILURE_CATEGORY = [
        BridgeErrorClass::NETWORK => 'NETWORK',
        BridgeErrorClass::AUTH => 'AUTH',
        BridgeErrorClass::VALIDATION => 'VALIDATION',
        BridgeErrorClass::PROVIDER => 'PROVIDER',
        BridgeErrorClass::UNKNOWN => 'UNKNOWN',
    ];

    private const ACCEPTABLE_RECEIVE_STATES = ['CREATED', 'READY', 'FAILED'];

    public function __construct(private EntityManager $entityManager) {}

    /**
     * Persist one validated terminal bridge result.
     *
     * Saving SendExecution deliberately triggers EmailLifecycleProjectionHook.
     * This service never loads, mutates, or saves a Lead directly.
     */
    public function receiveResult(SendExecutionBridgeResult $result): void
    {
        $execution = $this->loadExecution($result->executionId());
        $currentStatus = (string) $execution->get('status');

        if ($currentStatus === 'CANCELLED') {
            throw new BridgeRejectionException('Execution is cancelled.');
        }
        if ($currentStatus === 'SENT') {
            $this->handleAlreadySent($execution, $result);

            return;
        }
        if (!in_array($currentStatus, self::ACCEPTABLE_RECEIVE_STATES, true)) {
            throw new BridgeRejectionException('Execution has an unsupported current status.');
        }

        if ($result->normalizedStatus() === BridgeNormalizedStatus::SENT) {
            $execution->set([
                'status' => 'SENT',
                'providerName' => 'Brevo',
                'providerMessageId' => $result->providerAttemptId(),
            ]);
            $this->entityManager->saveEntity($execution);
            $this->ensureSentEmailEvent($execution, $result);

            return;
        }

        $execution->set([
            'status' => 'FAILED',
            'failureCategory' => $this->failureCategory($result->errorClass()),
            'lastError' => $result->errorCode(),
            'retryCount' => ((int) ($execution->get('retryCount') ?? 0)) + 1,
        ]);
        $this->entityManager->saveEntity($execution);
    }

    private function loadExecution(string $executionId): Entity
    {
        $execution = $this->entityManager->getRDBRepository('SendExecution')
            ->where(['sendRequestId' => $executionId])
            ->findOne();
        if (!$execution) {
            throw new BridgeRejectionException('Unknown execution: ' . $executionId);
        }

        return $execution;
    }

    private function handleAlreadySent(Entity $execution, SendExecutionBridgeResult $result): void
    {
        if ($result->normalizedStatus() !== BridgeNormalizedStatus::SENT) {
            throw new BridgeRejectionException('Execution already SENT.');
        }
        if ($execution->get('providerMessageId') !== $result->providerAttemptId()) {
            throw new BridgeRejectionException('Execution already SENT with another provider message ID.');
        }

        $this->ensureSentEmailEvent($execution, $result);
    }

    private function ensureSentEmailEvent(Entity $execution, SendExecutionBridgeResult $result): void
    {
        $providerMessageId = $result->providerAttemptId();
        if ($providerMessageId === null) {
            throw new BridgeRejectionException('SENT result requires provider_attempt_id.');
        }
        $leadId = $execution->get('leadId');
        if (!is_string($leadId) || $leadId === '') {
            throw new BridgeRejectionException('SendExecution requires a Lead link.');
        }

        $existing = $this->entityManager->getRDBRepository('EmailEvent')
            ->where([
                'externalMessageId' => $providerMessageId,
                'eventType' => 'SENT',
            ])
            ->findOne();
        if ($existing) {
            if ($existing->get('leadId') !== $leadId) {
                throw new BridgeRejectionException('EmailEvent external message ID belongs to another Lead.');
            }

            return;
        }

        $event = $this->entityManager->getEntity('EmailEvent');
        $event->set([
            'name' => 'Send: ' . $providerMessageId,
            'externalMessageId' => $providerMessageId,
            'eventType' => 'SENT',
            'eventAt' => $result->occurredAt()->format('Y-m-d H:i:s'),
            'source' => 'CONNECTOR_SYNC',
            'leadId' => $leadId,
        ]);
        $this->entityManager->saveEntity($event);
    }

    private function failureCategory(?string $errorClass): string
    {
        $category = self::ERROR_CLASS_TO_FAILURE_CATEGORY[$errorClass ?? ''] ?? null;
        if ($category === null) {
            throw new BridgeRejectionException('Unknown error class: ' . ($errorClass ?? 'null'));
        }

        return $category;
    }
}
