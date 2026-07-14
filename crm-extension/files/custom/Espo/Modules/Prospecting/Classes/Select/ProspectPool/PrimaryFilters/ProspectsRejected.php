<?php

namespace Espo\Modules\Prospecting\Classes\Select\ProspectPool\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class ProspectsRejected implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['qualificationStatus' => 'REJECTED']);
    }
}
