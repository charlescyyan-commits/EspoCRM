<?php

namespace Espo\Modules\Prospecting\Classes\Select\SalesFeedback\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class PositiveFeedback implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['outcome' => 'POSITIVE']);
    }
}
