<?php

namespace Espo\Modules\Prospecting\Classes\Select\SalesFeedback\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class RecentFeedback implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['createdAt>=' => date('Y-m-d H:i:s', strtotime('-14 days'))]);
    }
}
