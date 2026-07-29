<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

/**
 * Provider-neutral identity and capability contract.
 *
 * External service behavior and transport details are outside this contract.
 */
interface ProviderContract
{
    public function providerType(): string;

    public function capabilities(): ProviderCapabilityDeclaration;
}
