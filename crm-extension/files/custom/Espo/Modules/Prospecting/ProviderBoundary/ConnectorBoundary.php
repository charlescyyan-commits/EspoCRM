<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

/**
 * Port implemented by connector-owned runtime outside the CRM module.
 */
interface ConnectorBoundary
{
    public function execute(
        ProviderExecutionRequest $request
    ): ProviderResultEnvelope;
}
