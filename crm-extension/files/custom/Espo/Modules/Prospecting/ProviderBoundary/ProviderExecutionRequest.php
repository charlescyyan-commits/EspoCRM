<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Authorized, provider-neutral request envelope handed to the connector port.
 *
 * CRM supplies governance references only. Provider inputs are addressed by
 * an opaque input reference and are not interpreted at this boundary.
 */
final class ProviderExecutionRequest
{
    public function __construct(
        private string $requestId,
        private string $providerType,
        private CredentialReference $credentialReference,
        private string $authorizationReference,
        private string $auditReference,
        private string $policyReference,
        private string $inputReference,
    ) {
        $this->requestId = $this->required($requestId, 'requestId');
        $this->providerType = ProviderTypeRegistry::assertAllowed($providerType);
        $this->authorizationReference = $this->required(
            $authorizationReference,
            'authorizationReference'
        );
        $this->auditReference = $this->required(
            $auditReference,
            'auditReference'
        );
        $this->policyReference = $this->required(
            $policyReference,
            'policyReference'
        );
        $this->inputReference = $this->required(
            $inputReference,
            'inputReference'
        );

        if (!$credentialReference->capabilities()->supports($this->providerType)) {
            throw new InvalidArgumentException(
                'Credential reference is not associated with the requested provider type.'
            );
        }
    }

    public function requestId(): string
    {
        return $this->requestId;
    }

    public function providerType(): string
    {
        return $this->providerType;
    }

    public function credentialReference(): CredentialReference
    {
        return $this->credentialReference;
    }

    public function authorizationReference(): string
    {
        return $this->authorizationReference;
    }

    public function auditReference(): string
    {
        return $this->auditReference;
    }

    public function policyReference(): string
    {
        return $this->policyReference;
    }

    public function inputReference(): string
    {
        return $this->inputReference;
    }

    private function required(string $value, string $field): string
    {
        $value = trim($value);
        if ($value === '') {
            throw new InvalidArgumentException("{$field} is required.");
        }

        return $value;
    }
}
