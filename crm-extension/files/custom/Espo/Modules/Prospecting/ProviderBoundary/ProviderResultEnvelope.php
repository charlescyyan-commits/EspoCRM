<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Sanitized result boundary containing references rather than provider output.
 */
final class ProviderResultEnvelope
{
    public const ACCEPTED = 'ACCEPTED';
    public const SUCCEEDED = 'SUCCEEDED';
    public const FAILED = 'FAILED';
    public const REJECTED = 'REJECTED';

    /** @var list<string> */
    private const STATUSES = [
        self::ACCEPTED,
        self::SUCCEEDED,
        self::FAILED,
        self::REJECTED,
    ];

    public function __construct(
        private string $requestId,
        private string $providerType,
        private string $status,
        private string $auditReference,
        private ?string $resultReference = null,
        private ?string $failureCategory = null,
    ) {
        $this->requestId = $this->required($requestId, 'requestId');
        $this->providerType = ProviderTypeRegistry::assertAllowed($providerType);
        $this->status = $this->allowedStatus($status);
        $this->auditReference = $this->required(
            $auditReference,
            'auditReference'
        );
        $this->resultReference = $this->optional($resultReference);
        $this->failureCategory = $this->optional($failureCategory);
    }

    public function requestId(): string
    {
        return $this->requestId;
    }

    public function providerType(): string
    {
        return $this->providerType;
    }

    public function status(): string
    {
        return $this->status;
    }

    public function auditReference(): string
    {
        return $this->auditReference;
    }

    public function resultReference(): ?string
    {
        return $this->resultReference;
    }

    public function failureCategory(): ?string
    {
        return $this->failureCategory;
    }

    private function allowedStatus(string $status): string
    {
        $status = trim($status);
        if (!in_array($status, self::STATUSES, true)) {
            throw new InvalidArgumentException(
                'Unsupported provider result status.'
            );
        }

        return $status;
    }

    private function required(string $value, string $field): string
    {
        $value = trim($value);
        if ($value === '') {
            throw new InvalidArgumentException("{$field} is required.");
        }

        return $value;
    }

    private function optional(?string $value): ?string
    {
        $value = trim((string) $value);

        return $value === '' ? null : $value;
    }
}
