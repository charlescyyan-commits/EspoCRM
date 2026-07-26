<?php

namespace Espo\Modules\Prospecting\Classes\Select\SendExecution\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

/**
 * C18 operational queue: Failed Send (status = FAILED).
 *
 * Server-side PrimaryFilter only. ACL remains on the Record select path.
 * Governance: adr-c18-sendexecution-v1
 */
class C18FailedSend implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['status' => 'FAILED']);
    }
}
