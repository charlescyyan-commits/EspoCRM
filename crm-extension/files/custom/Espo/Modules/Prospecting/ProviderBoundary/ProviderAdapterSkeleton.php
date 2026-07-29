<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Boundary-only base for a connector-owned adapter implementation.
 *
 * The CRM extension provides no concrete adapter and no execution behavior.
 */
abstract class ProviderAdapterSkeleton implements
    ProviderContract,
    ConnectorBoundary
{
    public function __construct(
        private string $providerType,
        private ProviderCapabilityDeclaration $capabilities,
    ) {
        $this->providerType = ProviderTypeRegistry::assertAllowed($providerType);
        if (!$capabilities->supports($this->providerType)) {
            throw new InvalidArgumentException(
                'Adapter capability declaration must include its provider type.'
            );
        }
    }

    final public function providerType(): string
    {
        return $this->providerType;
    }

    final public function capabilities(): ProviderCapabilityDeclaration
    {
        return $this->capabilities;
    }

    abstract public function execute(
        ProviderExecutionRequest $request
    ): ProviderResultEnvelope;
}
