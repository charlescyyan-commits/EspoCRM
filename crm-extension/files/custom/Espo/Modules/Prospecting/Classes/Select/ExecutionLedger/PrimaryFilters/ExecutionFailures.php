<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Classes\Select\ExecutionLedger\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

final class ExecutionFailures implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['eventType' => 'EXECUTION_FAILED']);
    }
}
