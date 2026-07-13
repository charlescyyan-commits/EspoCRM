<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class PeProposalReviewRequired implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'peProposalEligibility' => true,
            'peProposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        ]);
    }
}
