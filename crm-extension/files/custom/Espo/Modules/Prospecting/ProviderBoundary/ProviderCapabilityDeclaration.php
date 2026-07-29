<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Declares only controlled capability categories at the governance boundary.
 *
 * Adapter-specific operations remain outside CRM and cannot extend this
 * declaration with vendor-owned types.
 */
final class ProviderCapabilityDeclaration
{
    /** @var list<string> */
    private array $providerTypes;

    /**
     * @param list<string> $providerTypes
     */
    public function __construct(array $providerTypes)
    {
        if ($providerTypes === []) {
            throw new InvalidArgumentException(
                'At least one provider capability is required.'
            );
        }

        $declared = [];
        foreach ($providerTypes as $providerType) {
            $declared[] = ProviderTypeRegistry::assertAllowed($providerType);
        }

        $declared = array_values(array_unique($declared));
        $this->providerTypes = array_values(
            array_intersect(ProviderTypeRegistry::all(), $declared)
        );
    }

    /**
     * @return list<string>
     */
    public function providerTypes(): array
    {
        return $this->providerTypes;
    }

    public function supports(string $providerType): bool
    {
        return in_array(
            ProviderTypeRegistry::assertAllowed($providerType),
            $this->providerTypes,
            true
        );
    }
}
