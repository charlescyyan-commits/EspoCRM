<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class PePendingOutreach implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(Cond::in(Cond::column('outreachStatus'), ['RESEARCH_COMPLETED', 'QUALIFIED']));
    }
}
