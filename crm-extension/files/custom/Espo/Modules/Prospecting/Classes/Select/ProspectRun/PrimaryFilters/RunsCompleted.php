<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Classes\Select\ProspectRun\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

final class RunsCompleted implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['status' => 'COMPLETED']);
    }
}
