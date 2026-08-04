<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

/** Save-option markers for WP4 Decision Support artifacts. */
final class Wp4DecisionSupportSaveOption
{
    public const CONTEXT_CREATE_AUTHORIZED =
        'c25.wp4DecisionSupportContextCreateAuthorized';

    public const CONTEXT_CLOSE_AUTHORIZED =
        'c25.wp4DecisionSupportContextCloseAuthorized';

    public const REVIEW_CREATE_AUTHORIZED =
        'c25.wp4HumanReviewDecisionRecordCreateAuthorized';

    public const REVIEW_TRANSITION_AUTHORIZED =
        'c25.wp4HumanReviewDecisionRecordTransitionAuthorized';

    public const FEEDBACK_CREATE_AUTHORIZED =
        'c25.wp4PresentationFeedbackCreateAuthorized';
}
