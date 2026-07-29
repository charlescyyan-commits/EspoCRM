<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Metadata-only reference to the existing C20 ProviderCredential custody row.
 *
 * This value object carries record identity, ownership, and capability
 * association only. It cannot resolve or activate external credentials.
 */
final class CredentialReference
{
    public function __construct(
        private string $referenceId,
        private string $ownerUserId,
        private ProviderCapabilityDeclaration $capabilities,
    ) {
        $this->referenceId = $this->required($referenceId, 'referenceId');
        $this->ownerUserId = $this->required($ownerUserId, 'ownerUserId');
    }

    public function referenceId(): string
    {
        return $this->referenceId;
    }

    public function ownerUserId(): string
    {
        return $this->ownerUserId;
    }

    public function capabilities(): ProviderCapabilityDeclaration
    {
        return $this->capabilities;
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
