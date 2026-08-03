<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

/** Internal save-option markers for CommercialBrief authorized mutations. */
final class CommercialBriefSaveOption
{
    public const PROPOSAL_CREATE_AUTHORIZED =
        'c25.commercialBriefProposalCreateAuthorized';

    public const REVIEW_TRANSITION_AUTHORIZED =
        'c25.commercialBriefReviewTransitionAuthorized';

    private function __construct()
    {
    }
}
