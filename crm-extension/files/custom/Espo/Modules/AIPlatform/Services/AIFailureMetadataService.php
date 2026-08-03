<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use DateTimeImmutable;
use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP5 Lite Failure Metadata Foundation service.
 *
 * Records failure context correlated to RT-WP4 Lite FAILED/BLOCKED outcomes.
 * Service-owned record contract only (no entity metadata / job-engine merge).
 * Does not invoke Connector, mutate ProviderBinding, resolve secrets, retry,
 * recover, reserve, or queue.
 */
final class AIFailureMetadataService
{
    public const INPUT_VALIDATION = 'validation_failure';
    public const INPUT_POLICY = 'policy_rejection';
    public const INPUT_BOUNDARY = 'boundary_rejection';
    public const INPUT_TIMEOUT = 'timeout_metadata';
    public const INPUT_UNKNOWN = 'unknown';

    /**
     * @var array<string, array{
     *   failureCode: string,
     *   correlatedFoundationState: string,
     *   requestIdentity: string,
     *   failureMessageSafe: string|null,
     *   correlationReference: string|null,
     *   sourceLayer: string|null,
     *   recordedAt: string
     * }>
     */
    private array $records = [];

    /**
     * Classify a foundation-visible input class into a Lite failure code.
     * Metadata-only: does not schedule recovery or retry.
     */
    public function classify(string $inputClass): string
    {
        $inputClass = trim(strtolower($inputClass));

        return match ($inputClass) {
            self::INPUT_VALIDATION, 'validation', 'validation_failed' => AIFailureMetadata::VALIDATION_FAILED,
            self::INPUT_POLICY, 'policy', 'policy_rejected' => AIFailureMetadata::POLICY_REJECTED,
            self::INPUT_BOUNDARY, 'boundary', 'boundary_rejected' => AIFailureMetadata::BOUNDARY_REJECTED,
            self::INPUT_TIMEOUT, 'timeout', 'timeout_metadata' => AIFailureMetadata::TIMEOUT_METADATA,
            self::INPUT_UNKNOWN, 'unknown', 'unknown_failure' => AIFailureMetadata::UNKNOWN_FAILURE,
            default => throw new BadRequest('AIFailureMetadataService classify rejects unknown input class.'),
        };
    }

    /**
     * Record failure metadata correlated to an RT-WP4 Lite terminal state.
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function record(array $input): array
    {
        AIFailureMetadataGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        if ($requestIdentity === '') {
            throw new BadRequest('AIFailureMetadataService record requires requestIdentity.');
        }

        $failureCode = trim((string) ($input['failureCode'] ?? ''));
        if ($failureCode === '' && isset($input['inputClass'])) {
            $failureCode = $this->classify((string) $input['inputClass']);
        }

        AIFailureMetadata::assertValid($failureCode);

        $foundationState = trim((string) ($input['correlatedFoundationState'] ?? ''));
        if ($foundationState === '') {
            throw new BadRequest('AIFailureMetadataService record requires correlatedFoundationState.');
        }

        AIFailureMetadataGuard::assertCorrelation($failureCode, $foundationState);

        $sourceLayer = $this->optionalString($input['sourceLayer'] ?? null);
        AIFailureMetadataGuard::assertSourceLayer($sourceLayer);

        $message = $this->optionalString($input['failureMessageSafe'] ?? null);
        $correlationReference = $this->optionalString($input['correlationReference'] ?? null);

        $record = [
            'failureCode' => $failureCode,
            'correlatedFoundationState' => $foundationState,
            'requestIdentity' => $requestIdentity,
            'failureMessageSafe' => $message,
            'correlationReference' => $correlationReference,
            'sourceLayer' => $sourceLayer,
            'recordedAt' => (new DateTimeImmutable('now'))->format('Y-m-d H:i:s'),
        ];

        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * Record metadata from an RT-WP4 Lite foundation state record (consume-only).
     *
     * Expected foundation record keys: foundationState, requestIdentity,
     * optional boundaryReference / provenanceReference / transitionReasonCode.
     *
     * @param array<string, mixed> $foundationRecord
     * @param array<string, mixed> $options
     * @return array<string, mixed>
     */
    public function recordFromFoundationState(array $foundationRecord, array $options = []): array
    {
        AIFailureMetadataGuard::assertSafeMutationPayload($foundationRecord);
        AIFailureMetadataGuard::assertSafeMutationPayload($options);

        $requestIdentity = trim((string) ($foundationRecord['requestIdentity'] ?? ''));
        $foundationState = trim((string) ($foundationRecord['foundationState'] ?? ''));

        if ($requestIdentity === '' || $foundationState === '') {
            throw new BadRequest(
                'recordFromFoundationState requires RT-WP4 requestIdentity and foundationState.'
            );
        }

        if (!in_array($foundationState, [AIFoundationState::FAILED, AIFoundationState::BLOCKED], true)) {
            throw new BadRequest(
                'recordFromFoundationState accepts only RT-WP4 FAILED or BLOCKED.'
            );
        }

        $failureCode = trim((string) ($options['failureCode'] ?? ''));
        if ($failureCode === '') {
            $failureCode = $this->classifyFromFoundationReason(
                $foundationState,
                trim((string) ($foundationRecord['transitionReasonCode'] ?? '')),
                trim((string) ($options['inputClass'] ?? ''))
            );
        }

        $sourceLayer = $this->optionalString($options['sourceLayer'] ?? null);
        if ($sourceLayer === null) {
            $sourceLayer = $foundationState === AIFoundationState::BLOCKED ? 'POLICY' : 'VALIDATION';
        }

        return $this->record([
            'requestIdentity' => $requestIdentity,
            'failureCode' => $failureCode,
            'correlatedFoundationState' => $foundationState,
            'failureMessageSafe' => $options['failureMessageSafe'] ?? null,
            'correlationReference' => $options['correlationReference']
                ?? $foundationRecord['boundaryReference']
                ?? $foundationRecord['provenanceReference']
                ?? null,
            'sourceLayer' => $sourceLayer,
        ]);
    }

    /**
     * @return array<string, mixed>|null
     */
    public function get(string $requestIdentity): ?array
    {
        $requestIdentity = trim($requestIdentity);

        return $this->records[$requestIdentity] ?? null;
    }

    private function classifyFromFoundationReason(
        string $foundationState,
        string $transitionReasonCode,
        string $inputClass,
    ): string {
        if ($inputClass !== '') {
            return $this->classify($inputClass);
        }

        if ($foundationState === AIFoundationState::BLOCKED) {
            if ($transitionReasonCode === AIFoundationStateService::REASON_POLICY) {
                return AIFailureMetadata::POLICY_REJECTED;
            }

            return AIFailureMetadata::BOUNDARY_REJECTED;
        }

        // FAILED
        if ($transitionReasonCode === AIFoundationStateService::REASON_VALIDATION) {
            return AIFailureMetadata::VALIDATION_FAILED;
        }

        if ($transitionReasonCode === AIFoundationStateService::REASON_CLOSE) {
            return AIFailureMetadata::UNKNOWN_FAILURE;
        }

        return AIFailureMetadata::UNKNOWN_FAILURE;
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
