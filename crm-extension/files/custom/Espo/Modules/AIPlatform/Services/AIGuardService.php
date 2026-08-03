<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * RT-WP7 Lite Runtime Guards Foundation service.
 *
 * Fail-closed runtime boundary validation composing RT-WP2–WP6 vocabularies.
 * Service-owned returned result contract only (no entity/ACL/workflow merge).
 * Does not grant permissions, run workflows, invoke Connector, resolve
 * secrets, authenticate providers, or flip invariant registry rows.
 *
 * Guard ≠ authorization engine.
 * Guard ≠ workflow engine.
 * Guard ≠ execution engine.
 */
final class AIGuardService
{
    /** @var list<string> */
    private const SECRET_FIELDS = [
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

    /** @var list<string> */
    private const C25_AUTHORITY_FIELDS = [
        'CommercialBrief',
        'Opportunity',
        'opportunityStage',
        'commercialDecision',
        'salesAuthority',
    ];

    /**
     * Validate a runtime boundary payload fail-closed.
     *
     * Checks payload safety first, then any present dimensions.
     *
     * @param array<string, mixed> $input
     */
    public function validate(array $input): AIGuardValidationResult
    {
        $payload = $this->validatePayloadSafety($input);
        if (!$payload->isAccepted()) {
            return $payload;
        }

        if (array_key_exists('capability', $input)) {
            $result = $this->validateCapability((string) $input['capability']);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        if (array_key_exists('purpose', $input)) {
            $result = $this->validatePurpose($input['purpose']);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        if (
            array_key_exists('providerBindingReference', $input)
            || array_key_exists('requireBindingReference', $input)
        ) {
            $require = (bool) ($input['requireBindingReference'] ?? true);
            $ref = $input['providerBindingReference'] ?? null;
            $result = $this->validateBindingReference($ref, $require);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        if (array_key_exists('foundationState', $input)) {
            $result = $this->validateFoundationState((string) $input['foundationState']);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        if (array_key_exists('failureCode', $input)) {
            $result = $this->validateFailureCode((string) $input['failureCode']);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        if (
            array_key_exists('reservationIntent', $input)
            || array_key_exists('ownerReference', $input)
        ) {
            $intent = (string) ($input['reservationIntent'] ?? '');
            $owner = $input['ownerReference'] ?? null;
            $result = $this->validateReservationOwnership($intent, $owner);
            if (!$result->isAccepted()) {
                return $result;
            }
        }

        return AIGuardValidationResult::accept(
            AIGuardRule::PAYLOAD_SAFETY,
            'Runtime guard boundary checks accepted.'
        );
    }

    public function validateCapability(string $capability): AIGuardValidationResult
    {
        $capability = trim($capability);

        if ($capability === '' || !in_array($capability, AIGuardRule::CAPABILITIES, true)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::CAPABILITY,
                'UNKNOWN_CAPABILITY',
                'Capability must be one of the five-value portfolio.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::CAPABILITY);
    }

    public function validatePurpose(mixed $purpose): AIGuardValidationResult
    {
        if ($purpose === null) {
            return AIGuardValidationResult::reject(
                AIGuardRule::PURPOSE,
                'PURPOSE_MISSING',
                'Purpose is required.'
            );
        }

        if (!is_string($purpose) && !is_numeric($purpose)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::PURPOSE,
                'PURPOSE_INVALID',
                'Purpose must be a non-secret string identifier.'
            );
        }

        $purpose = trim((string) $purpose);
        if ($purpose === '') {
            return AIGuardValidationResult::reject(
                AIGuardRule::PURPOSE,
                'PURPOSE_MISSING',
                'Purpose must not be empty.'
            );
        }

        if ($this->containsSecretNeedle($purpose) || strcasecmp($purpose, 'COMMERCIAL_BRIEF') === 0) {
            return AIGuardValidationResult::reject(
                AIGuardRule::PURPOSE,
                'COMMERCIAL_BRIEF_FORBIDDEN',
                'Purpose must not equal a CompletionCapability portfolio identity.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::PURPOSE);
    }

    public function validateBindingReference(mixed $reference, bool $required = true): AIGuardValidationResult
    {
        if ($reference === null || (is_string($reference) && trim($reference) === '')) {
            if ($required) {
                return AIGuardValidationResult::reject(
                    AIGuardRule::BINDING_REFERENCE,
                    'BINDING_REFERENCE_MISSING',
                    'ProviderBinding reference is required.'
                );
            }

            return AIGuardValidationResult::accept(AIGuardRule::BINDING_REFERENCE);
        }

        if (!is_string($reference) && !is_numeric($reference)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::BINDING_REFERENCE,
                'SECRET_SHAPED_INPUT',
                'ProviderBinding reference must be a non-secret scalar reference.'
            );
        }

        $reference = trim((string) $reference);
        if ($this->containsSecretNeedle($reference)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::BINDING_REFERENCE,
                'SECRET_SHAPED_INPUT',
                'ProviderBinding reference must not carry secret-shaped values.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::BINDING_REFERENCE);
    }

    public function validateFoundationState(string $state): AIGuardValidationResult
    {
        $state = trim($state);

        if (in_array($state, AIFoundationState::FORBIDDEN, true)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::FOUNDATION_STATE,
                'INVALID_FOUNDATION_STATE',
                'Execution-engine or deferred states are rejected.'
            );
        }

        if ($state === '' || !AIFoundationState::isKnown($state)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::FOUNDATION_STATE,
                'INVALID_FOUNDATION_STATE',
                'Foundation state must be one of the six Lite states.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::FOUNDATION_STATE);
    }

    public function validateFailureCode(string $failureCode): AIGuardValidationResult
    {
        $failureCode = trim($failureCode);

        if (in_array($failureCode, AIFailureMetadata::FORBIDDEN, true)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::FAILURE_CODE,
                'INVALID_FAILURE_CODE',
                'Retry/provider/deferred failure labels are rejected.'
            );
        }

        if ($failureCode === '' || !AIFailureMetadata::isKnown($failureCode)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::FAILURE_CODE,
                'INVALID_FAILURE_CODE',
                'Failure code must be one of the five Lite failure codes.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::FAILURE_CODE);
    }

    public function validateReservationOwnership(string $intent, mixed $ownerReference): AIGuardValidationResult
    {
        $intent = trim($intent);

        if (in_array($intent, AIReservationMetadata::FORBIDDEN, true)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::RESERVATION_INTENT,
                'INVALID_RESERVATION_INTENT',
                'Lock/execution reservation labels are rejected.'
            );
        }

        if ($intent === '' || !AIReservationMetadata::isKnown($intent)) {
            return AIGuardValidationResult::reject(
                AIGuardRule::RESERVATION_INTENT,
                'INVALID_RESERVATION_INTENT',
                'Reservation intent must be one of the five Lite intents.'
            );
        }

        $owner = null;
        if ($ownerReference !== null) {
            if (!is_string($ownerReference) && !is_numeric($ownerReference)) {
                return AIGuardValidationResult::reject(
                    AIGuardRule::RESERVATION_INTENT,
                    'SECRET_SHAPED_INPUT',
                    'Owner reference must be a non-secret scalar.'
                );
            }
            $owner = trim((string) $ownerReference);
            if ($this->containsSecretNeedle($owner)) {
                return AIGuardValidationResult::reject(
                    AIGuardRule::RESERVATION_INTENT,
                    'SECRET_SHAPED_INPUT',
                    'Owner reference must not carry secret-shaped values.'
                );
            }
        }

        if (AIReservationMetadata::requiresOwner($intent) && ($owner === null || $owner === '')) {
            return AIGuardValidationResult::reject(
                AIGuardRule::RESERVATION_INTENT,
                'OWNER_REFERENCE_REQUIRED',
                'Owner reference is required when reservationIntent is not NONE.'
            );
        }

        return AIGuardValidationResult::accept(AIGuardRule::RESERVATION_INTENT);
    }

    /**
     * @param array<string, mixed> $input
     */
    public function validatePayloadSafety(array $input): AIGuardValidationResult
    {
        foreach (array_keys($input) as $fieldName) {
            $name = (string) $fieldName;

            foreach (self::SECRET_FIELDS as $blocked) {
                if (strcasecmp($name, $blocked) === 0) {
                    return AIGuardValidationResult::reject(
                        AIGuardRule::PAYLOAD_SAFETY,
                        'SECRET_SHAPED_INPUT',
                        'Secret-shaped mutation fields are rejected.'
                    );
                }
            }

            foreach (self::C25_AUTHORITY_FIELDS as $blocked) {
                if (strcasecmp($name, $blocked) === 0) {
                    return AIGuardValidationResult::reject(
                        AIGuardRule::PAYLOAD_SAFETY,
                        'C25_AUTHORITY_FORBIDDEN',
                        'C25/Opportunity/sales authority fields are rejected.'
                    );
                }
            }

            $lower = strtolower($name);
            if (
                str_contains($lower, 'queue')
                || str_contains($lower, 'worker')
                || str_contains($lower, 'retry')
                || str_contains($lower, 'scheduler')
                || str_contains($lower, 'mutex')
                || str_contains($lower, 'locktoken')
                || str_contains($lower, 'workflow')
                || str_contains($lower, 'permission')
                || str_contains($lower, 'aclrole')
            ) {
                return AIGuardValidationResult::reject(
                    AIGuardRule::PAYLOAD_SAFETY,
                    'EXECUTION_CONTROL_FORBIDDEN',
                    'Execution-control or authorization-engine fields are rejected.'
                );
            }
        }

        foreach ($input as $value) {
            if (!is_string($value) && !is_numeric($value)) {
                continue;
            }

            if ($this->containsSecretNeedle(trim((string) $value))) {
                return AIGuardValidationResult::reject(
                    AIGuardRule::PAYLOAD_SAFETY,
                    'SECRET_SHAPED_INPUT',
                    'Secret-shaped mutation values are rejected.'
                );
            }
        }

        return AIGuardValidationResult::accept(AIGuardRule::PAYLOAD_SAFETY);
    }

    private function containsSecretNeedle(string $value): bool
    {
        $lower = strtolower($value);
        if ($lower === '') {
            return false;
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
                return true;
            }
        }

        return false;
    }
}
