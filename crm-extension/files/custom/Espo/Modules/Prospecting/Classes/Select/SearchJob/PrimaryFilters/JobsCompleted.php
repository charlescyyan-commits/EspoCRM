<?php

namespace Espo\Modules\Prospecting\Classes\Select\SearchJob\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class JobsCompleted implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['status' => 'COMPLETED']);
    }
}
