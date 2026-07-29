<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Execution;

use Espo\Modules\Prospecting\ProviderBoundary\ProviderExecutionRequest;
use Espo\Modules\Prospecting\ProviderBoundary\ProviderTypeRegistry;
use InvalidArgumentException;

/**
 * Immutable representation of one proposed provider-neutral external action.
 *
 * Persistence remains with ActionGate and ExecutionLedger. This value object
 * introduces no duplicate action entity or provider runtime.
 */
final class ExecutionAction
{
    public function __construct(
        private string $actionId,
        private string $prospectCandidateId,
        private string $prospectRunId,
        private string $providerType,
        private ProviderExecutionRequest $request,
    ) {
        $this->actionId = $this->required($actionId, 'actionId');
        $this->prospectCandidateId = $this->required(
            $prospectCandidateId,
            'prospectCandidateId'
        );
        $this->prospectRunId = $this->required(
            $prospectRunId,
            'prospectRunId'
        );
        $this->providerType = ProviderTypeRegistry::assertAllowed(
            $providerType
        );

        if ($request->providerType() !== $this->providerType) {
            throw new InvalidArgumentException(
                'Execution action and provider request types must match.'
            );
        }
    }

    public function actionId(): string
    {
        return $this->actionId;
    }

    public function prospectCandidateId(): string
    {
        return $this->prospectCandidateId;
    }

    public function prospectRunId(): string
    {
        return $this->prospectRunId;
    }

    public function providerType(): string
    {
        return $this->providerType;
    }

    public function request(): ProviderExecutionRequest
    {
        return $this->request;
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
