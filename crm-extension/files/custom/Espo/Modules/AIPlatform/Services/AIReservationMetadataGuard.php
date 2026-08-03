<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Fail-closed validation for RT-WP6 Lite reservation metadata.
 *
 * Policy validation only. Not a lock, mutex, Redis/DB lock, queue, worker,
 * scheduler, or reservation-execution component.
 */
final class AIReservationMetadataGuard
{
    /**
     * Allowed intent edges (metadata-only):
     * NONE              → DECLARED
     * DECLARED          → HELD_METADATA | CONFLICT | RELEASED_METADATA | NONE
     * HELD_METADATA     → CONFLICT | RELEASED_METADATA
     * CONFLICT          → RELEASED_METADATA
     * RELEASED_METADATA → DECLARED | NONE
     *
     * @var array<string, list<string>>
     */
    private const ALLOWED = [
        AIReservationMetadata::NONE => [AIReservationMetadata::DECLARED],
        AIReservationMetadata::DECLARED => [
            AIReservationMetadata::HELD_METADATA,
            AIReservationMetadata::CONFLICT,
            AIReservationMetadata::RELEASED_METADATA,
            AIReservationMetadata::NONE,
        ],
        AIReservationMetadata::HELD_METADATA => [
            AIReservationMetadata::CONFLICT,
            AIReservationMetadata::RELEASED_METADATA,
        ],
        AIReservationMetadata::CONFLICT => [AIReservationMetadata::RELEASED_METADATA],
        AIReservationMetadata::RELEASED_METADATA => [
            AIReservationMetadata::DECLARED,
            AIReservationMetadata::NONE,
        ],
    ];

    /** @var list<string> */
    private const BLOCKED_MUTATION_FIELDS = [
        'apiKey',
        'apiSecret',
        'token',
        'password',
        'secret',
        'accessToken',
        'refreshToken',
        'privateKey',
        'plaintextCredential',
        'encryptedSecret',
        'lockToken',
        'leaseId',
        'mutexKey',
        'redisLock',
        'nextRetryAt',
        'attemptCount',
        'retryCount',
        'retryPolicy',
    ];

    public static function assertTransition(string $from, string $to): void
    {
        AIReservationMetadata::assertValid($from);
        AIReservationMetadata::assertValid($to);

        $allowed = self::ALLOWED[$from] ?? [];
        if (!in_array($to, $allowed, true)) {
            throw new BadRequest(
                "AIReservationMetadata illegal intent transition from {$from} to {$to}."
            );
        }
    }

    public static function assertOwnerReference(string $reservationIntent, ?string $ownerReference): void
    {
        AIReservationMetadata::assertValid($reservationIntent);

        $ownerReference = $ownerReference === null ? null : trim($ownerReference);

        if (AIReservationMetadata::requiresOwner($reservationIntent)) {
            if ($ownerReference === null || $ownerReference === '') {
                throw new BadRequest(
                    'AIReservationMetadata requires ownerReference when reservationIntent is not NONE.'
                );
            }
        }
    }

    public static function assertOwnershipScope(?string $ownershipScope): void
    {
        if ($ownershipScope === null) {
            return;
        }

        $ownershipScope = trim($ownershipScope);
        if ($ownershipScope === '') {
            return;
        }

        if (!in_array($ownershipScope, AIReservationMetadata::OWNERSHIP_SCOPES, true)) {
            throw new BadRequest('AIReservationMetadata ownershipScope must be REQUEST or BOUNDARY.');
        }
    }

    public static function assertConflictReason(?string $conflictReasonCode): void
    {
        if ($conflictReasonCode === null) {
            return;
        }

        $conflictReasonCode = trim($conflictReasonCode);
        if ($conflictReasonCode === '') {
            return;
        }

        if (!in_array($conflictReasonCode, AIReservationMetadata::CONFLICT_REASONS, true)) {
            throw new BadRequest(
                'AIReservationMetadata conflictReasonCode must be OWNER_MISMATCH, DUPLICATE_INTENT, or UNKNOWN_CONFLICT.'
            );
        }
    }

    /**
     * Reject secret-shaped or execution-control mutation payloads.
     *
     * @param array<string, mixed> $payload
     */
    public static function assertSafeMutationPayload(array $payload): void
    {
        foreach (array_keys($payload) as $fieldName) {
            $name = (string) $fieldName;
            foreach (self::BLOCKED_MUTATION_FIELDS as $blocked) {
                if (strcasecmp($name, $blocked) === 0) {
                    throw new BadRequest('AIReservationMetadata rejects secret or lock/execution-control mutation fields.');
                }
            }

            $lower = strtolower($name);
            if (
                str_contains($lower, 'queue')
                || str_contains($lower, 'worker')
                || str_contains($lower, 'retry')
                || str_contains($lower, 'scheduler')
                || str_contains($lower, 'mutex')
                || str_contains($lower, 'redis')
                || str_contains($lower, 'locktoken')
                || str_contains($lower, 'recovery')
            ) {
                throw new BadRequest('AIReservationMetadata rejects forbidden execution-control mutation fields.');
            }
        }

        foreach ($payload as $value) {
            if (!is_string($value) && !is_numeric($value)) {
                continue;
            }

            $lower = strtolower(trim((string) $value));
            if ($lower === '') {
                continue;
            }

            $needles = [
                'sk' . '-',
                'bearer' . ' ',
                'api' . '_key=',
                'api' . 'key=',
                'ey' . 'j',
                '-----' . 'begin',
            ];
            foreach ($needles as $needle) {
                if (str_contains($lower, $needle)) {
                    throw new BadRequest('AIReservationMetadata rejects secret-shaped mutation values.');
                }
            }
        }
    }

    /**
     * @return array<string, list<string>>
     */
    public static function allowedMatrix(): array
    {
        return self::ALLOWED;
    }
}
