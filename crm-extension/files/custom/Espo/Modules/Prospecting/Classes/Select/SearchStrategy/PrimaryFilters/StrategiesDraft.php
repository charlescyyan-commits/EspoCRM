<?php

namespace Espo\Modules\Prospecting\Classes\Select\SearchStrategy\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class StrategiesDraft implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['status' => 'DRAFT']);
    }
}
