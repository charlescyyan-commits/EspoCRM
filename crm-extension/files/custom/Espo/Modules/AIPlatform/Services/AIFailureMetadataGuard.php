<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Fail-closed validation for RT-WP5 Lite failure metadata.
 *
 * Policy validation only. Not a worker, queue, retry, recovery, or reservation
 * component.
 */
final class AIFailureMetadataGuard
{
    /**
     * Allowed correlatedFoundationState values per failure code.
     *
     * @var array<string, list<string>>
     */
    private const ALLOWED_CORRELATION = [
        AIFailureMetadata::VALIDATION_FAILED => [AIFoundationState::FAILED],
        AIFailureMetadata::POLICY_REJECTED => [AIFoundationState::BLOCKED],
        AIFailureMetadata::BOUNDARY_REJECTED => [
            AIFoundationState::BLOCKED,
            AIFoundationState::FAILED,
        ],
        AIFailureMetadata::TIMEOUT_METADATA => [AIFoundationState::FAILED],
        AIFailureMetadata::UNKNOWN_FAILURE => [AIFoundationState::FAILED],
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
        'nextRetryAt',
        'attemptCount',
        'retryCount',
        'maxRetries',
        'retryPolicy',
        'retrySchedule',
    ];

    public static function assertCorrelation(string $failureCode, string $foundationState): void
    {
        AIFailureMetadata::assertValid($failureCode);

        $foundationState = trim($foundationState);
        if (!in_array($foundationState, [AIFoundationState::FAILED, AIFoundationState::BLOCKED], true)) {
            throw new BadRequest(
                'AIFailureMetadata correlates only to RT-WP4 FAILED or BLOCKED.'
            );
        }

        $allowed = self::ALLOWED_CORRELATION[$failureCode] ?? [];
        if (!in_array($foundationState, $allowed, true)) {
            throw new BadRequest(
                "AIFailureMetadata illegal correlation of {$failureCode} to {$foundationState}."
            );
        }
    }

    public static function assertSourceLayer(?string $sourceLayer): void
    {
        if ($sourceLayer === null) {
            return;
        }

        $sourceLayer = trim($sourceLayer);
        if ($sourceLayer === '') {
            return;
        }

        if (!in_array($sourceLayer, AIFailureMetadata::SOURCE_LAYERS, true)) {
            throw new BadRequest('AIFailureMetadata sourceLayer must be FOUNDATION, POLICY, or VALIDATION.');
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
                    throw new BadRequest('AIFailureMetadata rejects secret or retry-control mutation fields.');
                }
            }

            $lower = strtolower($name);
            if (
                str_contains($lower, 'queue')
                || str_contains($lower, 'worker')
                || str_contains($lower, 'retry')
                || str_contains($lower, 'reservation')
                || str_contains($lower, 'scheduler')
                || str_contains($lower, 'recovery')
            ) {
                throw new BadRequest('AIFailureMetadata rejects forbidden execution-control mutation fields.');
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
                    throw new BadRequest('AIFailureMetadata rejects secret-shaped mutation values.');
                }
            }
        }
    }

    /**
     * @return array<string, list<string>>
     */
    public static function allowedCorrelationMatrix(): array
    {
        return self::ALLOWED_CORRELATION;
    }
}
