<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP7 Lite non-secret guard validation result.
 *
 * Represents accept/reject only. Does not grant permissions, start workflows,
 * or execute outbound calls.
 */
final class AIGuardValidationResult
{
    private function __construct(
        private bool $accepted,
        private string $ruleId,
        private ?string $reasonCode,
        private ?string $detailsSafe,
    ) {
    }

    public static function accept(string $ruleId, ?string $detailsSafe = null): self
    {
        AIGuardRule::assertValid($ruleId);

        return new self(true, trim($ruleId), null, self::optionalSafe($detailsSafe));
    }

    public static function reject(string $ruleId, string $reasonCode, ?string $detailsSafe = null): self
    {
        AIGuardRule::assertValid($ruleId);

        $reasonCode = trim($reasonCode);
        if ($reasonCode === '' || !AIGuardRule::isKnownReason($reasonCode)) {
            throw new BadRequest('AIGuardValidationResult reject requires a ratified reasonCode.');
        }

        return new self(false, trim($ruleId), $reasonCode, self::optionalSafe($detailsSafe));
    }

    public function isAccepted(): bool
    {
        return $this->accepted;
    }

    public function getRuleId(): string
    {
        return $this->ruleId;
    }

    public function getReasonCode(): ?string
    {
        return $this->reasonCode;
    }

    public function getDetailsSafe(): ?string
    {
        return $this->detailsSafe;
    }

    /**
     * @return array{
     *   accepted: bool,
     *   ruleId: string,
     *   reasonCode: string|null,
     *   detailsSafe: string|null
     * }
     */
    public function toArray(): array
    {
        return [
            'accepted' => $this->accepted,
            'ruleId' => $this->ruleId,
            'reasonCode' => $this->reasonCode,
            'detailsSafe' => $this->detailsSafe,
        ];
    }

    private static function optionalSafe(?string $detailsSafe): ?string
    {
        if ($detailsSafe === null) {
            return null;
        }

        $trimmed = trim($detailsSafe);

        return $trimmed === '' ? null : $trimmed;
    }
}
