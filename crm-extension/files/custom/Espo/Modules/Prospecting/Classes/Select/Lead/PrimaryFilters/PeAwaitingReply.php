<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class PeAwaitingReply implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['outreachStatus' => 'CONTACTED']);
    }
}
