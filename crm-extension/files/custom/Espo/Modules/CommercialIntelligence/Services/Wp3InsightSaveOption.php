<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

/** Save-option markers for WP3 CommercialInsight / BusinessReviewContext. */
final class Wp3InsightSaveOption
{
    public const INSIGHT_CREATE_AUTHORIZED =
        'c25.wp3CommercialInsightCreateAuthorized';

    public const INSIGHT_REVIEW_TRANSITION_AUTHORIZED =
        'c25.wp3CommercialInsightReviewTransitionAuthorized';

    public const REVIEW_CONTEXT_CREATE_AUTHORIZED =
        'c25.wp3BusinessReviewContextCreateAuthorized';

    public const REVIEW_CONTEXT_CLOSE_AUTHORIZED =
        'c25.wp3BusinessReviewContextCloseAuthorized';

    private function __construct()
    {
    }
}
