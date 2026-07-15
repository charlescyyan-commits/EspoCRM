<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

final class BridgeErrorClass
{
    public const NETWORK = 'NETWORK';
    public const AUTH = 'AUTH';
    public const VALIDATION = 'VALIDATION';
    public const PROVIDER = 'PROVIDER';
    public const UNKNOWN = 'UNKNOWN';

    /** @return list<string> */
    public static function values(): array
    {
        return [
            self::NETWORK,
            self::AUTH,
            self::VALIDATION,
            self::PROVIDER,
            self::UNKNOWN,
        ];
    }
}
