<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Fail-closed transition validation for RT-WP4 Lite foundation states.
 *
 * Policy validation only. Not a worker, queue, retry, or reservation component.
 */
final class AIFoundationStateTransitionGuard
{
    /**
     * Allowed edges:
     * REQUESTED  → VALIDATING
     * VALIDATING → READY | BLOCKED | FAILED
     * READY      → COMPLETED | FAILED
     *
     * @var array<string, list<string>>
     */
    private const ALLOWED = [
        AIFoundationState::REQUESTED => [AIFoundationState::VALIDATING],
        AIFoundationState::VALIDATING => [
            AIFoundationState::READY,
            AIFoundationState::BLOCKED,
            AIFoundationState::FAILED,
        ],
        AIFoundationState::READY => [
            AIFoundationState::COMPLETED,
            AIFoundationState::FAILED,
        ],
        AIFoundationState::BLOCKED => [],
        AIFoundationState::COMPLETED => [],
        AIFoundationState::FAILED => [],
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
    ];

    public static function assertTransition(string $from, string $to): void
    {
        AIFoundationState::assertValid($from);
        AIFoundationState::assertValid($to);

        $allowed = self::ALLOWED[$from] ?? [];
        if (!in_array($to, $allowed, true)) {
            throw new BadRequest(
                "AIFoundationState illegal transition from {$from} to {$to}."
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
                    throw new BadRequest('AIFoundationState rejects secret-shaped mutation fields.');
                }
            }

            $lower = strtolower($name);
            if (
                str_contains($lower, 'queue')
                || str_contains($lower, 'worker')
                || str_contains($lower, 'retry')
                || str_contains($lower, 'reservation')
                || str_contains($lower, 'cancelreason')
            ) {
                throw new BadRequest('AIFoundationState rejects forbidden execution-control mutation fields.');
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
                    throw new BadRequest('AIFoundationState rejects secret-shaped mutation values.');
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
