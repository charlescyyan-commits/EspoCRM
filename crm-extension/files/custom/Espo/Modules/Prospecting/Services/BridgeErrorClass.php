<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/**
 * Terminal bridge failure taxonomy.
 *
 * C20 WP0.4 parity: RATE_LIMIT already exists on SendExecution.failureCategory /
 * provider contracts and is added here for BridgeErrorClass parity. QUOTA and
 * CONTENT_FILTER are new. This class classifies errors only — it does not own
 * retry scheduling or SendExecution lifecycle transitions.
 */
final class BridgeErrorClass
{
    public const NETWORK = 'NETWORK';
    public const AUTH = 'AUTH';
    public const VALIDATION = 'VALIDATION';
    public const PROVIDER = 'PROVIDER';
    public const UNKNOWN = 'UNKNOWN';
    /** Existing elsewhere; BridgeErrorClass parity. */
    public const RATE_LIMIT = 'RATE_LIMIT';
    /** New C20 taxonomy class. */
    public const QUOTA = 'QUOTA';
    /** New C20 taxonomy class. */
    public const CONTENT_FILTER = 'CONTENT_FILTER';

    /** @return list<string> */
    public static function values(): array
    {
        return [
            self::NETWORK,
            self::AUTH,
            self::VALIDATION,
            self::PROVIDER,
            self::UNKNOWN,
            self::RATE_LIMIT,
            self::QUOTA,
            self::CONTENT_FILTER,
        ];
    }

    /**
     * Taxonomy-level auto-retry eligibility (ADR-C20 §4.3).
     *
     * Does not schedule retries or mutate SendExecution — retry policy ownership
     * remains outside this class.
     */
    public static function isAutoRetryEligible(string $errorClass): bool
    {
        return in_array($errorClass, [
            self::NETWORK,
            self::PROVIDER,
            self::RATE_LIMIT,
        ], true);
    }
}
