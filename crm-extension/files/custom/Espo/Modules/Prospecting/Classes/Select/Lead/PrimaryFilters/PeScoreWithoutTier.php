<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class PeScoreWithoutTier implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder
            ->where(Cond::notEqual(Cond::column('peOpportunityScoreV4'), null))
            ->where(Cond::or(
                Cond::equal(Cond::column('peScoreTier'), null),
                Cond::equal(Cond::column('peScoreTier'), '')
            ));
    }
}
