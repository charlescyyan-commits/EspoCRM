<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use DateTimeImmutable;
use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP6 Lite Ownership & Reservation Metadata Foundation service.
 *
 * Records ownership / reservation intent metadata only. Service-owned record
 * contract only (no entity metadata / Redis / job-engine merge). Does not
 * acquire locks, invoke Connector, mutate ProviderBinding, resolve secrets,
 * retry, recover, queue, or suppress provider calls.
 *
 * Reservation metadata ≠ reservation execution.
 */
final class AIReservationMetadataService
{
    /**
     * @var array<string, array{
     *   requestIdentity: string,
     *   ownerReference: string|null,
     *   reservationIntent: string,
     *   ownershipScope: string|null,
     *   correlationReference: string|null,
     *   conflictReference: string|null,
     *   conflictReasonCode: string|null,
     *   recordedAt: string
     * }>
     */
    private array $records = [];

    /**
     * Begin metadata tracking with intent NONE (no owner required).
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function begin(array $input): array
    {
        AIReservationMetadataGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        if ($requestIdentity === '') {
            throw new BadRequest('AIReservationMetadataService begin requires requestIdentity.');
        }

        $record = $this->makeRecord(
            $requestIdentity,
            null,
            AIReservationMetadata::NONE,
            $this->optionalString($input['ownershipScope'] ?? null),
            $this->optionalString($input['correlationReference'] ?? null),
            null,
            null,
        );
        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * Apply an explicit validated intent transition / ownership update.
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function transition(array $input): array
    {
        AIReservationMetadataGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        $to = trim((string) ($input['reservationIntent'] ?? ''));

        if ($requestIdentity === '' || !isset($this->records[$requestIdentity])) {
            throw new BadRequest('AIReservationMetadataService transition requires an existing requestIdentity.');
        }

        $current = $this->records[$requestIdentity];
        $from = (string) $current['reservationIntent'];

        // Idempotent same-intent re-record for HELD_METADATA with same owner.
        if (
            $from === AIReservationMetadata::HELD_METADATA
            && $to === AIReservationMetadata::HELD_METADATA
        ) {
            $owner = $this->optionalString($input['ownerReference'] ?? $current['ownerReference']);
            if ($owner !== null && $owner === $current['ownerReference']) {
                return $this->refreshHeld($requestIdentity, $current, $input);
            }
        }

        AIReservationMetadataGuard::assertTransition($from, $to);

        $ownerReference = $this->optionalString($input['ownerReference'] ?? $current['ownerReference']);
        if ($to === AIReservationMetadata::NONE) {
            $ownerReference = null;
        }

        AIReservationMetadataGuard::assertOwnerReference($to, $ownerReference);
        AIReservationMetadataGuard::assertOwnershipScope(
            $this->optionalString($input['ownershipScope'] ?? $current['ownershipScope'])
        );

        $conflictReference = $this->optionalString($input['conflictReference'] ?? null);
        $conflictReasonCode = $this->optionalString($input['conflictReasonCode'] ?? null);
        if ($to !== AIReservationMetadata::CONFLICT) {
            $conflictReference = null;
            $conflictReasonCode = null;
        } else {
            AIReservationMetadataGuard::assertConflictReason($conflictReasonCode);
            if ($conflictReasonCode === null) {
                $conflictReasonCode = 'UNKNOWN_CONFLICT';
            }
        }

        $record = $this->makeRecord(
            $requestIdentity,
            $ownerReference,
            $to,
            $this->optionalString($input['ownershipScope'] ?? $current['ownershipScope']),
            $this->optionalString($input['correlationReference'] ?? $current['correlationReference']),
            $conflictReference,
            $conflictReasonCode,
        );
        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * Declare ownership intent (NONE → DECLARED).
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function declare(array $input): array
    {
        $input['reservationIntent'] = AIReservationMetadata::DECLARED;

        return $this->transition($input);
    }

    /**
     * Record logical hold metadata (DECLARED → HELD_METADATA).
     * If already HELD_METADATA by another owner, records CONFLICT (metadata only).
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function holdMetadata(array $input): array
    {
        AIReservationMetadataGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        if ($requestIdentity === '' || !isset($this->records[$requestIdentity])) {
            throw new BadRequest('AIReservationMetadataService holdMetadata requires an existing requestIdentity.');
        }

        $current = $this->records[$requestIdentity];
        $ownerReference = $this->optionalString($input['ownerReference'] ?? null);
        AIReservationMetadataGuard::assertOwnerReference(AIReservationMetadata::HELD_METADATA, $ownerReference);

        if ($current['reservationIntent'] === AIReservationMetadata::HELD_METADATA) {
            if ($ownerReference === $current['ownerReference']) {
                return $this->refreshHeld($requestIdentity, $current, $input);
            }

            return $this->transition([
                'requestIdentity' => $requestIdentity,
                'reservationIntent' => AIReservationMetadata::CONFLICT,
                'ownerReference' => $current['ownerReference'],
                'conflictReference' => $ownerReference,
                'conflictReasonCode' => 'OWNER_MISMATCH',
                'ownershipScope' => $input['ownershipScope'] ?? $current['ownershipScope'],
                'correlationReference' => $input['correlationReference'] ?? $current['correlationReference'],
            ]);
        }

        $input['reservationIntent'] = AIReservationMetadata::HELD_METADATA;

        return $this->transition($input);
    }

    /**
     * Release metadata hold/conflict (→ RELEASED_METADATA).
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function releaseMetadata(array $input): array
    {
        $input['reservationIntent'] = AIReservationMetadata::RELEASED_METADATA;

        return $this->transition($input);
    }

    /**
     * @return array<string, mixed>|null
     */
    public function get(string $requestIdentity): ?array
    {
        $requestIdentity = trim($requestIdentity);

        return $this->records[$requestIdentity] ?? null;
    }

    /**
     * @param array<string, mixed> $current
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    private function refreshHeld(string $requestIdentity, array $current, array $input): array
    {
        $record = $this->makeRecord(
            $requestIdentity,
            $current['ownerReference'],
            AIReservationMetadata::HELD_METADATA,
            $this->optionalString($input['ownershipScope'] ?? $current['ownershipScope']),
            $this->optionalString($input['correlationReference'] ?? $current['correlationReference']),
            null,
            null,
        );
        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * @return array{
     *   requestIdentity: string,
     *   ownerReference: string|null,
     *   reservationIntent: string,
     *   ownershipScope: string|null,
     *   correlationReference: string|null,
     *   conflictReference: string|null,
     *   conflictReasonCode: string|null,
     *   recordedAt: string
     * }
     */
    private function makeRecord(
        string $requestIdentity,
        ?string $ownerReference,
        string $reservationIntent,
        ?string $ownershipScope,
        ?string $correlationReference,
        ?string $conflictReference,
        ?string $conflictReasonCode,
    ): array {
        AIReservationMetadata::assertValid($reservationIntent);
        AIReservationMetadataGuard::assertOwnerReference($reservationIntent, $ownerReference);
        AIReservationMetadataGuard::assertOwnershipScope($ownershipScope);
        AIReservationMetadataGuard::assertConflictReason($conflictReasonCode);

        return [
            'requestIdentity' => $requestIdentity,
            'ownerReference' => $ownerReference,
            'reservationIntent' => $reservationIntent,
            'ownershipScope' => $ownershipScope,
            'correlationReference' => $correlationReference,
            'conflictReference' => $conflictReference,
            'conflictReasonCode' => $conflictReasonCode,
            'recordedAt' => (new DateTimeImmutable('now'))->format('Y-m-d H:i:s'),
        ];
    }

    private function optionalString(mixed $value): ?string
    {
        if ($value === null) {
            return null;
        }

        $trimmed = trim((string) $value);

        return $trimmed === '' ? null : $trimmed;
    }
}
