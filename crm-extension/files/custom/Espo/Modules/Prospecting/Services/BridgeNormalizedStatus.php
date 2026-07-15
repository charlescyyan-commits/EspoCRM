<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

final class BridgeNormalizedStatus
{
    public const SENT = 'SENT';
    public const FAILED = 'FAILED';

    /** @return list<string> */
    public static function values(): array
    {
        return [self::SENT, self::FAILED];
    }
}
