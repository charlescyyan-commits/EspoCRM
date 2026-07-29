<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\ProviderBoundary;

use InvalidArgumentException;

/**
 * Closed governance vocabulary for provider-neutral capability categories.
 */
final class ProviderTypeRegistry
{
    public const SEARCH = 'SEARCH';
    public const ENRICHMENT = 'ENRICHMENT';
    public const AI_RESEARCH = 'AI_RESEARCH';
    public const OUTREACH = 'OUTREACH';

    /** @var list<string> */
    private const TYPES = [
        self::SEARCH,
        self::ENRICHMENT,
        self::AI_RESEARCH,
        self::OUTREACH,
    ];

    /**
     * @return list<string>
     */
    public static function all(): array
    {
        return self::TYPES;
    }

    public static function assertAllowed(string $providerType): string
    {
        $providerType = trim($providerType);
        if (!in_array($providerType, self::TYPES, true)) {
            throw new InvalidArgumentException('Unsupported provider type.');
        }

        return $providerType;
    }

    private function __construct()
    {
    }
}
