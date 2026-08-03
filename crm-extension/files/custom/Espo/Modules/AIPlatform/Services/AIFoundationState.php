<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP4 Lite closed foundation-state vocabulary.
 *
 * Not an execution engine. Does not define job/queue/worker/retry states.
 */
final class AIFoundationState
{
    public const REQUESTED = 'REQUESTED';
    public const VALIDATING = 'VALIDATING';
    public const READY = 'READY';
    public const BLOCKED = 'BLOCKED';
    public const COMPLETED = 'COMPLETED';
    public const FAILED = 'FAILED';

    /** @var list<string> */
    public const ALL = [
        self::REQUESTED,
        self::VALIDATING,
        self::READY,
        self::BLOCKED,
        self::COMPLETED,
        self::FAILED,
    ];

    /** @var list<string> */
    public const TERMINAL = [
        self::BLOCKED,
        self::COMPLETED,
        self::FAILED,
    ];

    /** Forbidden engine / deferred states for this Lite vocabulary. */
    /** @var list<string> */
    public const FORBIDDEN = [
        'QUEUED',
        'RUNNING',
        'RETRY_PENDING',
        'RESERVATION_CONFLICT',
        'CANCELLED',
        'DISPATCHED',
        'PROVIDER_TIMEOUT',
        'EXECUTION_COMPLETED',
    ];

    public static function assertValid(string $state): void
    {
        $state = trim($state);

        if (in_array($state, self::FORBIDDEN, true)) {
            throw new BadRequest('AIFoundationState rejects execution-engine or deferred states.');
        }

        if ($state === '' || !in_array($state, self::ALL, true)) {
            throw new BadRequest('AIFoundationState must be exactly one of the six Lite foundation states.');
        }
    }

    public static function isTerminal(string $state): bool
    {
        return in_array(trim($state), self::TERMINAL, true);
    }

    public static function isKnown(string $state): bool
    {
        return in_array(trim($state), self::ALL, true);
    }
}
