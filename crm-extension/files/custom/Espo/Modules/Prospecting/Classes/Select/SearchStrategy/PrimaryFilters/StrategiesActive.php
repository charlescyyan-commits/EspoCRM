<?php

namespace Espo\Modules\Prospecting\Classes\Select\SearchStrategy\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\Part\Expression as Expr;
use Espo\ORM\Query\SelectBuilder;

class StrategiesActive implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(
            Cond::in(Expr::column('status'), ['GENERATED', 'RUNNING'])
        );
    }
}
