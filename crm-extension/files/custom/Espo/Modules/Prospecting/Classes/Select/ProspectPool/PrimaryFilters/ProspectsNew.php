<?php

namespace Espo\Modules\Prospecting\Classes\Select\ProspectPool\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class ProspectsNew implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'queue' => 'DISCOVERY',
            'status' => 'WAITING',
        ]);
    }
}
