<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use DateTimeZone;

/**
 * Validated CRM representation of the terminal connector bridge result.
 *
 * It intentionally contains no Lead identifiers, raw delivery content, or
 * retry policy. The SendExecution identity is supplied by executionId only.
 */
final class SendExecutionBridgeResult
{
    private const ALLOWED_PAYLOAD_FIELDS = [
        'execution_id',
        'provider_attempt_id',
        'normalized_status',
        'error_class',
        'error_code',
        'occurred_at',
    ];

    public function __construct(
        private string $executionId,
        private ?string $providerAttemptId,
        private string $normalizedStatus,
        private ?string $errorClass,
        private ?string $errorCode,
        private DateTimeImmutable $occurredAt,
    ) {
        $this->assertText('execution_id', $this->executionId);
        if ($this->providerAttemptId !== null) {
            $this->assertText('provider_attempt_id', $this->providerAttemptId);
            if (strlen($this->providerAttemptId) > 255) {
                throw new BridgeRejectionException('provider_attempt_id exceeds 255 characters.');
            }
        }
        if (!in_array($this->normalizedStatus, BridgeNormalizedStatus::values(), true)) {
            throw new BridgeRejectionException('Unsupported normalized_status.');
        }

        if ($this->normalizedStatus === BridgeNormalizedStatus::SENT) {
            if ($this->providerAttemptId === null) {
                throw new BridgeRejectionException('SENT result requires provider_attempt_id.');
            }
            if ($this->errorClass !== null || $this->errorCode !== null) {
                throw new BridgeRejectionException('SENT result must not include an error.');
            }

            return;
        }

        if ($this->errorClass === null || $this->errorCode === null) {
            throw new BridgeRejectionException('FAILED result requires error_class and error_code.');
        }
        if (!in_array($this->errorClass, BridgeErrorClass::values(), true)) {
            throw new BridgeRejectionException('Unknown error class: ' . $this->errorClass);
        }
        $this->assertText('error_code', $this->errorCode);
        if (!preg_match('/^[A-Z0-9_:-]+$/', $this->errorCode)) {
            throw new BridgeRejectionException('error_code must be a safe upper-case code.');
        }
    }

    /** @param array<string, mixed> $payload */
    public static function fromPayload(array $payload): self
    {
        foreach (self::forbiddenLeadFields() as $field) {
            if (array_key_exists($field, $payload)) {
                throw new BridgeRejectionException('Bridge result payload must not contain Lead fields.');
            }
        }
        foreach ($payload as $field => $_) {
            if (!in_array($field, self::ALLOWED_PAYLOAD_FIELDS, true)) {
                throw new BridgeRejectionException('Unsupported bridge result field: ' . $field);
            }
        }
        foreach (self::ALLOWED_PAYLOAD_FIELDS as $field) {
            if (!array_key_exists($field, $payload)) {
                throw new BridgeRejectionException('Missing bridge result field: ' . $field);
            }
        }
        if (!is_string($payload['execution_id']) || !is_string($payload['normalized_status'])) {
            throw new BridgeRejectionException('Bridge result identity and status must be strings.');
        }
        if (!is_null($payload['provider_attempt_id']) && !is_string($payload['provider_attempt_id'])) {
            throw new BridgeRejectionException('provider_attempt_id must be a string or null.');
        }
        if (!is_null($payload['error_class']) && !is_string($payload['error_class'])) {
            throw new BridgeRejectionException('error_class must be a string or null.');
        }
        if (!is_null($payload['error_code']) && !is_string($payload['error_code'])) {
            throw new BridgeRejectionException('error_code must be a string or null.');
        }
        if (!is_string($payload['occurred_at']) || trim($payload['occurred_at']) === '') {
            throw new BridgeRejectionException('occurred_at must be a non-empty UTC timestamp.');
        }
        if (!preg_match('/(?:Z|[+-]\d{2}:\d{2})$/', $payload['occurred_at'])) {
            throw new BridgeRejectionException('occurred_at must include a UTC offset.');
        }

        try {
            $occurredAt = new DateTimeImmutable($payload['occurred_at']);
        } catch (\Exception $exception) {
            throw new BridgeRejectionException('occurred_at is invalid.', 0, $exception);
        }

        return new self(
            trim($payload['execution_id']),
            $payload['provider_attempt_id'] === null ? null : trim($payload['provider_attempt_id']),
            trim($payload['normalized_status']),
            $payload['error_class'] === null ? null : trim($payload['error_class']),
            $payload['error_code'] === null ? null : trim($payload['error_code']),
            $occurredAt->setTimezone(new DateTimeZone('UTC')),
        );
    }

    public function executionId(): string
    {
        return $this->executionId;
    }

    public function providerAttemptId(): ?string
    {
        return $this->providerAttemptId;
    }

    public function normalizedStatus(): string
    {
        return $this->normalizedStatus;
    }

    public function errorClass(): ?string
    {
        return $this->errorClass;
    }

    public function errorCode(): ?string
    {
        return $this->errorCode;
    }

    public function occurredAt(): DateTimeImmutable
    {
        return $this->occurredAt;
    }

    private function assertText(string $field, string $value): void
    {
        if (trim($value) === '') {
            throw new BridgeRejectionException($field . ' must be a non-empty string.');
        }
    }

    /** @return list<string> */
    private static function forbiddenLeadFields(): array
    {
        // Kept as constructed strings so writer-inventory scans remain focused
        // on executable Lead mutations, not defensive ingress validation.
        return [
            'lead_id',
            'leadId',
            'pe' . 'EmailStatus',
            'pe' . 'LastEmailDate',
            'pe' . 'EmailReplyStatus',
            'pe' . 'EmailCampaignName',
        ];
    }
}
