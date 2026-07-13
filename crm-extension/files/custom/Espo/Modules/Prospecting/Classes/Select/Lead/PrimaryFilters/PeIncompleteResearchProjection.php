<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class PeIncompleteResearchProjection implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder
            ->where(['peResearchStatus' => 'COMPLETED'])
            ->where(Cond::or(
                Cond::equal(Cond::column('peResearchSummary'), null),
                Cond::equal(Cond::column('peResearchSummary'), ''),
                Cond::equal(Cond::column('peKeyEvidence'), null),
                Cond::equal(Cond::column('peKeyEvidence'), ''),
                Cond::equal(Cond::column('peRecommendedApproach'), null),
                Cond::equal(Cond::column('peRecommendedApproach'), '')
            ));
    }
}
