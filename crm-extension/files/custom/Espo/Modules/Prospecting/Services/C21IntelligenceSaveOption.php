<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/**
 * Internal create markers for immutable C21 intelligence records.
 */
final class C21IntelligenceSaveOption
{
    public const INSIGHT_CREATE_AUTHORIZED =
        'c21.aiQualificationInsightCreateAuthorized';
    public const HUMAN_FEEDBACK_CREATE_AUTHORIZED =
        'c21.humanFeedbackCreateAuthorized';

    private function __construct()
    {
    }
}
