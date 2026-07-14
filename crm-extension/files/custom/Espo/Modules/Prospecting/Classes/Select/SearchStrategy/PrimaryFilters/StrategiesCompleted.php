<?php

namespace Espo\Modules\Prospecting\Classes\Select\SearchStrategy\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class StrategiesCompleted implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['status' => 'COMPLETED']);
    }
}
