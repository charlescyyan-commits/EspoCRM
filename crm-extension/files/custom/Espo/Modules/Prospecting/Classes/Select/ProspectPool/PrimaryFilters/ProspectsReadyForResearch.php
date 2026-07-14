<?php

namespace Espo\Modules\Prospecting\Classes\Select\ProspectPool\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class ProspectsReadyForResearch implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'researchStatus' => 'PENDING',
            'qualificationStatus' => 'QUALIFIED',
        ]);
    }
}
