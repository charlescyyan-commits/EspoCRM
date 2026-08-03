<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP5 Lite closed failure-metadata vocabulary.
 *
 * Records foundation-visible failure context only. Does not define retry,
 * recovery, queue, worker, or provider-execution semantics.
 */
final class AIFailureMetadata
{
    public const VALIDATION_FAILED = 'VALIDATION_FAILED';
    public const POLICY_REJECTED = 'POLICY_REJECTED';
    public const BOUNDARY_REJECTED = 'BOUNDARY_REJECTED';
    public const TIMEOUT_METADATA = 'TIMEOUT_METADATA';
    public const UNKNOWN_FAILURE = 'UNKNOWN_FAILURE';

    /** @var list<string> */
    public const ALL = [
        self::VALIDATION_FAILED,
        self::POLICY_REJECTED,
        self::BOUNDARY_REJECTED,
        self::TIMEOUT_METADATA,
        self::UNKNOWN_FAILURE,
    ];

    /** Forbidden engine / deferred labels for this Lite vocabulary. */
    /** @var list<string> */
    public const FORBIDDEN = [
        'RETRY_PENDING',
        'RETRY_SCHEDULED',
        'QUEUED',
        'RUNNING',
        'NETWORK',
        'PROVIDER',
        'AUTH',
        'RATE_LIMIT',
        'QUOTA',
        'CONTENT_FILTER',
        'COMMERCIAL_BRIEF',
    ];

    /** @var list<string> */
    public const SOURCE_LAYERS = [
        'FOUNDATION',
        'POLICY',
        'VALIDATION',
    ];

    public static function assertValid(string $failureCode): void
    {
        $failureCode = trim($failureCode);

        if (in_array($failureCode, self::FORBIDDEN, true)) {
            throw new BadRequest('AIFailureMetadata rejects retry/provider/deferred failure labels.');
        }

        if ($failureCode === '' || !in_array($failureCode, self::ALL, true)) {
            throw new BadRequest('AIFailureMetadata must be exactly one of the five Lite failure codes.');
        }
    }

    public static function isKnown(string $failureCode): bool
    {
        return in_array(trim($failureCode), self::ALL, true);
    }
}
