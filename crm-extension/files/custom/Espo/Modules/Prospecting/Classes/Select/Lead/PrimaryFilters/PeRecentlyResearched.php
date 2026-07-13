<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

/**
 * Leads with research completed in the last 14 days.
 */
class PeRecentlyResearched implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'peResearchStatus' => 'COMPLETED',
            'peLastResearchedAt>=' => date('Y-m-d H:i:s', strtotime('-14 days')),
        ]);
    }
}
