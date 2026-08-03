<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * References-only execution boundary for Dispatch Foundation Lite.
 *
 * Assembled after eligibility succeeds. Does not invoke, execute, call a
 * connector, open HTTP, or carry secrets.
 */
final class AIDispatchExecutionBoundary
{
    /**
     * @param list<string> $providerBindingReferences
     */
    public function __construct(
        private string $requestIdentity,
        private string $purposeReference,
        private string $capabilityReference,
        private array $providerBindingReferences,
        private ?string $credentialReference,
        private ?string $provenanceReference,
        private ?string $policyVersionReference = null,
        private ?string $healthInputReference = null,
    ) {}

    public function getRequestIdentity(): string
    {
        return $this->requestIdentity;
    }

    public function getPurposeReference(): string
    {
        return $this->purposeReference;
    }

    public function getCapabilityReference(): string
    {
        return $this->capabilityReference;
    }

    /**
     * @return list<string>
     */
    public function getProviderBindingReferences(): array
    {
        return $this->providerBindingReferences;
    }

    /**
     * Custody reference only — never a resolved secret.
     */
    public function getCredentialReference(): ?string
    {
        return $this->credentialReference;
    }

    public function getProvenanceReference(): ?string
    {
        return $this->provenanceReference;
    }

    public function getPolicyVersionReference(): ?string
    {
        return $this->policyVersionReference;
    }

    public function getHealthInputReference(): ?string
    {
        return $this->healthInputReference;
    }

    /**
     * @return array{
     *   requestIdentity: string,
     *   purposeReference: string,
     *   capabilityReference: string,
     *   providerBindingReferences: list<string>,
     *   credentialReference: string|null,
     *   provenanceReference: string|null,
     *   policyVersionReference: string|null,
     *   healthInputReference: string|null
     * }
     */
    public function toArray(): array
    {
        return [
            'requestIdentity' => $this->requestIdentity,
            'purposeReference' => $this->purposeReference,
            'capabilityReference' => $this->capabilityReference,
            'providerBindingReferences' => $this->providerBindingReferences,
            'credentialReference' => $this->credentialReference,
            'provenanceReference' => $this->provenanceReference,
            'policyVersionReference' => $this->policyVersionReference,
            'healthInputReference' => $this->healthInputReference,
        ];
    }
}
