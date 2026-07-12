<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

/**
 * Leads synced from Chitu in the last 14 days.
 */
class PeRecentlySynced implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'peSyncStatus' => 'SYNCED',
            'peLastSyncAt>=' => date('Y-m-d H:i:s', strtotime('-14 days')),
        ]);
    }
}
