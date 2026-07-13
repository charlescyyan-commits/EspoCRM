<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

/**
 * Leads ready for outreach (CONTACT_READY pipeline state).
 */
class PeContactReady implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'outreachStatus' => 'CONTACT_READY',
        ]);
    }
}
