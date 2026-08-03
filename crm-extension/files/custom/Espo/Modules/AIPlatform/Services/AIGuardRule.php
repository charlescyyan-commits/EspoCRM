<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * RT-WP7 Lite closed guard dimension / rule identifiers.
 *
 * Fail-closed runtime validation dimensions only. Not an ACL, permission,
 * role, workflow, or execution-engine vocabulary.
 *
 * Guard ≠ authorization engine.
 * Guard ≠ workflow engine.
 * Guard ≠ execution engine.
 */
final class AIGuardRule
{
    public const CAPABILITY = 'CAPABILITY';
    public const PURPOSE = 'PURPOSE';
    public const BINDING_REFERENCE = 'BINDING_REFERENCE';
    public const FOUNDATION_STATE = 'FOUNDATION_STATE';
    public const FAILURE_CODE = 'FAILURE_CODE';
    public const RESERVATION_INTENT = 'RESERVATION_INTENT';
    public const PAYLOAD_SAFETY = 'PAYLOAD_SAFETY';

    /** @var list<string> */
    public const ALL = [
        self::CAPABILITY,
        self::PURPOSE,
        self::BINDING_REFERENCE,
        self::FOUNDATION_STATE,
        self::FAILURE_CODE,
        self::RESERVATION_INTENT,
        self::PAYLOAD_SAFETY,
    ];

    /** @var list<string> */
    public const CAPABILITIES = [
        'RESEARCH_EVIDENCE',
        'QUALIFICATION_INSIGHT',
        'DRAFT_ASSISTANCE',
        'REPLY_ASSISTANCE',
        'COMMERCIAL_BRIEF',
    ];

    /** @var list<string> */
    public const REASON_CODES = [
        'UNKNOWN_CAPABILITY',
        'COMMERCIAL_BRIEF_FORBIDDEN',
        'PURPOSE_MISSING',
        'PURPOSE_INVALID',
        'BINDING_REFERENCE_MISSING',
        'SECRET_SHAPED_INPUT',
        'INVALID_FOUNDATION_STATE',
        'INVALID_FAILURE_CODE',
        'INVALID_RESERVATION_INTENT',
        'OWNER_REFERENCE_REQUIRED',
        'EXECUTION_CONTROL_FORBIDDEN',
        'C25_AUTHORITY_FORBIDDEN',
    ];

    public static function assertValid(string $ruleId): void
    {
        $ruleId = trim($ruleId);

        if ($ruleId === '' || !in_array($ruleId, self::ALL, true)) {
            throw new BadRequest('AIGuardRule must be exactly one of the seven Lite guard dimensions.');
        }
    }

    public static function isKnown(string $ruleId): bool
    {
        return in_array(trim($ruleId), self::ALL, true);
    }

    public static function isKnownReason(string $reasonCode): bool
    {
        return in_array(trim($reasonCode), self::REASON_CODES, true);
    }
}
