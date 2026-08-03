<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use DateTimeImmutable;
use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP4 Lite Execution State Foundation service.
 *
 * Tracks foundation state around RT-WP3 Lite outcomes. Service-owned record
 * contract only (no entity metadata / job-engine merge). Does not invoke Connector,
 * mutate ProviderBinding, resolve secrets, retry, reserve, or queue.
 */
final class AIFoundationStateService
{
    public const REASON_POLICY = 'policy';
    public const REASON_VALIDATION = 'validation';
    public const REASON_CLOSE = 'close';

    /**
     * @var array<string, array{
     *   foundationState: string,
     *   requestIdentity: string,
     *   previousState: string|null,
     *   boundaryReference: string|null,
     *   transitionReasonCode: string|null,
     *   provenanceReference: string|null,
     *   updatedAt: string
     * }>
     */
    private array $records = [];

    /**
     * Begin foundation tracking for a governed request identity.
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function begin(array $input): array
    {
        AIFoundationStateTransitionGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        if ($requestIdentity === '') {
            throw new BadRequest('AIFoundationStateService begin requires requestIdentity.');
        }

        $provenanceReference = $this->optionalString($input['provenanceReference'] ?? null);

        $record = $this->makeRecord(
            AIFoundationState::REQUESTED,
            $requestIdentity,
            null,
            null,
            self::REASON_VALIDATION,
            $provenanceReference,
        );
        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * Apply an explicit validated transition.
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function transition(array $input): array
    {
        AIFoundationStateTransitionGuard::assertSafeMutationPayload($input);

        $requestIdentity = trim((string) ($input['requestIdentity'] ?? ''));
        $to = trim((string) ($input['toState'] ?? ''));
        $reason = trim((string) ($input['transitionReasonCode'] ?? self::REASON_VALIDATION));

        if ($requestIdentity === '' || !isset($this->records[$requestIdentity])) {
            throw new BadRequest('AIFoundationStateService transition requires an existing requestIdentity.');
        }

        if (!in_array($reason, [self::REASON_POLICY, self::REASON_VALIDATION, self::REASON_CLOSE], true)) {
            throw new BadRequest('transitionReasonCode must be policy, validation, or close.');
        }

        $current = $this->records[$requestIdentity];
        $from = (string) $current['foundationState'];

        AIFoundationStateTransitionGuard::assertTransition($from, $to);

        $boundaryReference = $this->optionalString($input['boundaryReference'] ?? $current['boundaryReference']);
        $provenanceReference = $this->optionalString(
            $input['provenanceReference'] ?? $current['provenanceReference']
        );

        $record = $this->makeRecord(
            $to,
            $requestIdentity,
            $from,
            $boundaryReference,
            $reason,
            $provenanceReference,
        );
        $this->records[$requestIdentity] = $record;

        return $record;
    }

    /**
     * Consume an RT-WP3 Lite resolve outcome and advance foundation state.
     *
     * Expected shape (from AIDispatchService::resolve):
     * eligibility, boundary (object|array|null), evaluationTrace, request.
     *
     * @param array<string, mixed> $dispatchOutcome
     * @return array<string, mixed>
     */
    public function applyDispatchOutcome(array $dispatchOutcome): array
    {
        AIFoundationStateTransitionGuard::assertSafeMutationPayload($dispatchOutcome);

        $request = $dispatchOutcome['request'] ?? null;
        if (!is_array($request)) {
            throw new BadRequest('applyDispatchOutcome requires RT-WP3 request array.');
        }

        $requestIdentity = trim((string) ($request['requestIdentity'] ?? ''));
        if ($requestIdentity === '') {
            throw new BadRequest('applyDispatchOutcome requires requestIdentity from RT-WP3 outcome.');
        }

        if (!isset($this->records[$requestIdentity])) {
            $this->begin([
                'requestIdentity' => $requestIdentity,
                'provenanceReference' => $request['provenanceReference'] ?? null,
            ]);
        }

        // REQUESTED → VALIDATING
        if ($this->records[$requestIdentity]['foundationState'] === AIFoundationState::REQUESTED) {
            $this->transition([
                'requestIdentity' => $requestIdentity,
                'toState' => AIFoundationState::VALIDATING,
                'transitionReasonCode' => self::REASON_VALIDATION,
                'provenanceReference' => $request['provenanceReference'] ?? null,
            ]);
        }

        $eligibility = trim((string) ($dispatchOutcome['eligibility'] ?? ''));
        $boundaryReference = $this->extractBoundaryReference($dispatchOutcome['boundary'] ?? null);

        if ($eligibility === AIDispatchService::CLASS_BOUND && $boundaryReference !== null) {
            return $this->transition([
                'requestIdentity' => $requestIdentity,
                'toState' => AIFoundationState::READY,
                'transitionReasonCode' => self::REASON_POLICY,
                'boundaryReference' => $boundaryReference,
                'provenanceReference' => $request['provenanceReference'] ?? null,
            ]);
        }

        if (in_array($eligibility, [
            AIDispatchService::CLASS_NOT_AUTHORIZED,
            AIDispatchService::CLASS_UNBOUND,
            AIDispatchService::CLASS_DISABLED,
            AIDispatchService::CLASS_PURPOSE_NOT_REGISTERED,
            AIDispatchService::CLASS_CAPABILITY_MISMATCH,
            AIDispatchService::CLASS_CREDENTIAL_REFERENCE_MISSING,
        ], true)) {
            return $this->transition([
                'requestIdentity' => $requestIdentity,
                'toState' => AIFoundationState::BLOCKED,
                'transitionReasonCode' => self::REASON_POLICY,
                'provenanceReference' => $request['provenanceReference'] ?? null,
            ]);
        }

        // Missing/empty eligibility or unresolved BOUND without boundary → FAILED.
        return $this->transition([
            'requestIdentity' => $requestIdentity,
            'toState' => AIFoundationState::FAILED,
            'transitionReasonCode' => self::REASON_VALIDATION,
            'provenanceReference' => $request['provenanceReference'] ?? null,
        ]);
    }

    /**
     * Close a READY foundation path for audit without outbound invoke.
     *
     * @param array<string, mixed> $input
     * @return array<string, mixed>
     */
    public function complete(array $input): array
    {
        $input['toState'] = AIFoundationState::COMPLETED;
        $input['transitionReasonCode'] = $input['transitionReasonCode'] ?? self::REASON_CLOSE;

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
     * @return array{
     *   foundationState: string,
     *   requestIdentity: string,
     *   previousState: string|null,
     *   boundaryReference: string|null,
     *   transitionReasonCode: string|null,
     *   provenanceReference: string|null,
     *   updatedAt: string
     * }
     */
    private function makeRecord(
        string $state,
        string $requestIdentity,
        ?string $previousState,
        ?string $boundaryReference,
        ?string $transitionReasonCode,
        ?string $provenanceReference,
    ): array {
        AIFoundationState::assertValid($state);

        return [
            'foundationState' => $state,
            'requestIdentity' => $requestIdentity,
            'previousState' => $previousState,
            'boundaryReference' => $boundaryReference,
            'transitionReasonCode' => $transitionReasonCode,
            'provenanceReference' => $provenanceReference,
            'updatedAt' => (new DateTimeImmutable('now'))->format('Y-m-d H:i:s'),
        ];
    }

    private function extractBoundaryReference(mixed $boundary): ?string
    {
        if ($boundary === null) {
            return null;
        }

        if (is_array($boundary)) {
            $refs = $boundary['providerBindingReferences'] ?? null;
            if (is_array($refs) && $refs !== []) {
                return trim((string) $refs[0]) ?: null;
            }

            $identity = $boundary['requestIdentity'] ?? null;

            return $this->optionalString($identity);
        }

        if ($boundary instanceof AIDispatchExecutionBoundary) {
            $refs = $boundary->getProviderBindingReferences();
            if ($refs !== []) {
                return $refs[0];
            }

            return $boundary->getRequestIdentity();
        }

        return null;
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
