<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP6 Lite closed reservation-intent vocabulary.
 *
 * Records ownership / reservation intent metadata only. Does not define lock,
 * mutex, Redis/DB lock, queue, worker, scheduler, or reservation-execution
 * semantics.
 *
 * Reservation metadata ≠ reservation execution.
 */
final class AIReservationMetadata
{
    public const NONE = 'NONE';
    public const DECLARED = 'DECLARED';
    public const HELD_METADATA = 'HELD_METADATA';
    public const CONFLICT = 'CONFLICT';
    public const RELEASED_METADATA = 'RELEASED_METADATA';

    /** @var list<string> */
    public const ALL = [
        self::NONE,
        self::DECLARED,
        self::HELD_METADATA,
        self::CONFLICT,
        self::RELEASED_METADATA,
    ];

    /** Forbidden lock / engine / deferred labels for this Lite vocabulary. */
    /** @var list<string> */
    public const FORBIDDEN = [
        'ACQUIRED',
        'LOCKED',
        'LEASED',
        'QUEUED',
        'CLAIMED_BY_WORKER',
        'PROVIDER_RESERVED',
        'RETRY_PENDING',
        'RECOVERING',
        'RESERVATION_EXECUTING',
        'COMMERCIAL_BRIEF',
    ];

    /** @var list<string> */
    public const OWNERSHIP_SCOPES = [
        'REQUEST',
        'BOUNDARY',
    ];

    /** @var list<string> */
    public const CONFLICT_REASONS = [
        'OWNER_MISMATCH',
        'DUPLICATE_INTENT',
        'UNKNOWN_CONFLICT',
    ];

    public static function assertValid(string $reservationIntent): void
    {
        $reservationIntent = trim($reservationIntent);

        if (in_array($reservationIntent, self::FORBIDDEN, true)) {
            throw new BadRequest('AIReservationMetadata rejects lock/execution/deferred reservation labels.');
        }

        if ($reservationIntent === '' || !in_array($reservationIntent, self::ALL, true)) {
            throw new BadRequest('AIReservationMetadata must be exactly one of the five Lite reservation intents.');
        }
    }

    public static function isKnown(string $reservationIntent): bool
    {
        return in_array(trim($reservationIntent), self::ALL, true);
    }

    public static function requiresOwner(string $reservationIntent): bool
    {
        return trim($reservationIntent) !== self::NONE;
    }
}
