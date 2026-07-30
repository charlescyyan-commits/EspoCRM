<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal write marker for the C23 feedback-learning boundary. */
final class C23FeedbackLearningSaveOption
{
    public const OBSERVATION_CREATE_AUTHORIZED =
        'c23.feedbackLearningObservationCreateAuthorized';

    private function __construct()
    {
    }
}
