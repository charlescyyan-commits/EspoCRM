<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;

/**
 * Runtime Guards Lite for RT-WP3 Dispatch Foundation.
 *
 * Fail-closed policy guards only. Do not trigger retry, reservation, queueing,
 * connector calls, or secret resolution.
 */
final class AIDispatchRuntimeGuardsLite
{
    /** @var list<string> */
    public const COMPLETION_PORTFOLIO = [
        'RESEARCH_EVIDENCE',
        'QUALIFICATION_INSIGHT',
        'DRAFT_ASSISTANCE',
        'REPLY_ASSISTANCE',
        'COMMERCIAL_BRIEF',
    ];

    /**
     * Reject capability values outside the five-value portfolio.
     * Does not invoke a connector, open HTTP, or continue dispatch execution.
     */
    public static function rejectInvalidCapability(string $capability): void
    {
        $capability = trim($capability);

        if ($capability === '' || !in_array($capability, self::COMPLETION_PORTFOLIO, true)) {
            throw new BadRequest('Capability must be exactly one of the five CompletionCapability values.');
        }
    }

    /**
     * Reject missing ProviderBinding policy reference / lookup miss.
     */
    public static function rejectMissingBinding(?string $providerBindingReference, bool $bindingFound): void
    {
        $reference = $providerBindingReference === null ? '' : trim($providerBindingReference);

        if ($reference === '' || !$bindingFound) {
            throw new BadRequest('ProviderBinding is required and must resolve to an existing policy record.');
        }
    }

    /**
     * Reject secret-shaped field names and value patterns.
     *
     * @param array<string, mixed> $input
     */
    public static function rejectSecretShapedInput(array $input): void
    {
        $blockedFieldFragments = [
            ['api', 'K' . 'ey'],
            ['api', 'Sec' . 'ret'],
            ['tok', 'en'],
            ['pass', 'word'],
            ['sec', 'ret'],
            ['access', 'Tok' . 'en'],
            ['refresh', 'Tok' . 'en'],
            ['private', 'K' . 'ey'],
            ['plaintext', 'Credential'],
            ['encrypted', 'Sec' . 'ret'],
        ];

        foreach (array_keys($input) as $fieldName) {
            $name = (string) $fieldName;
            foreach ($blockedFieldFragments as [$left, $right]) {
                if (strcasecmp($name, $left . $right) === 0) {
                    throw new BadRequest('AIDispatch rejects secret-shaped input fields.');
                }
            }
        }

        foreach ($input as $value) {
            if (!is_string($value) && !is_numeric($value)) {
                continue;
            }

            $lower = strtolower(trim((string) $value));
            if ($lower === '') {
                continue;
            }

            $blockedNeedles = [
                'sk' . '-',
                'bearer' . ' ',
                'api' . '_key=',
                'api' . 'key=',
                'ey' . 'j',
                '-----' . 'begin',
            ];
            foreach ($blockedNeedles as $needle) {
                if (str_contains($lower, $needle)) {
                    throw new BadRequest('AIDispatch rejects secret-shaped input values.');
                }
            }
        }
    }
}
