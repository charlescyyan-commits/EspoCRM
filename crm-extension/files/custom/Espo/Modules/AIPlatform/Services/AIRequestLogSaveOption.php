<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * Internal save option used only by AIRequestLogService when appending evidence.
 */
final class AIRequestLogSaveOption
{
    public const AI_REQUEST_LOG_CREATE_AUTHORIZED = 'aiRequestLogCreateAuthorized';

    private function __construct()
    {
    }
}
