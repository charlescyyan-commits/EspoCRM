<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Dispatch Foundation Lite request contract.
 *
 * Policy request only. Does not execute, invoke a connector, or resolve secrets.
 */
final class AIDispatchRequest
{
    /**
     * @param array<string, mixed> $input
     */
    public static function fromArray(array $input): self
    {
        AIDispatchRuntimeGuardsLite::rejectSecretShapedInput($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        $purposeReference = trim((string) ($input['purposeReference'] ?? ''));
        $capabilityReference = trim((string) ($input['capabilityReference'] ?? ''));
        $providerBindingReference = trim((string) ($input['providerBindingReference'] ?? ''));
        $provenanceReference = trim((string) ($input['provenanceReference'] ?? ''));

        if ($requestIdentity === '') {
            throw new BadRequest('AIDispatchRequest requires requestIdentity.');
        }

        if ($purposeReference === '') {
            throw new BadRequest('AIDispatchRequest requires purposeReference.');
        }

        if ($capabilityReference === '') {
            throw new BadRequest('AIDispatchRequest requires capabilityReference.');
        }

        return new self(
            $requestIdentity,
            $purposeReference,
            $capabilityReference,
            $providerBindingReference === '' ? null : $providerBindingReference,
            $provenanceReference === '' ? null : $provenanceReference,
        );
    }

    private function __construct(
        private string $requestIdentity,
        private string $purposeReference,
        private string $capabilityReference,
        private ?string $providerBindingReference,
        private ?string $provenanceReference,
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

    public function getProviderBindingReference(): ?string
    {
        return $this->providerBindingReference;
    }

    public function getProvenanceReference(): ?string
    {
        return $this->provenanceReference;
    }

    /**
     * @return array{
     *   requestIdentity: string,
     *   purposeReference: string,
     *   capabilityReference: string,
     *   providerBindingReference: string|null,
     *   provenanceReference: string|null
     * }
     */
    public function toArray(): array
    {
        return [
            'requestIdentity' => $this->requestIdentity,
            'purposeReference' => $this->purposeReference,
            'capabilityReference' => $this->capabilityReference,
            'providerBindingReference' => $this->providerBindingReference,
            'provenanceReference' => $this->provenanceReference,
        ];
    }
}
