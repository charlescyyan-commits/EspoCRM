<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class PeMissingBestFirstProduct implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(Cond::or(
            Cond::equal(Cond::column('peBestFirstProduct'), null),
            Cond::equal(Cond::column('peBestFirstProduct'), '')
        ));
    }
}
