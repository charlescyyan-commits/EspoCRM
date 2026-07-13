<?php

namespace Espo\Modules\Prospecting\Classes\Select\SalesFeedback\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class NeedsFollowUp implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(Cond::in(Cond::column('feedbackType'), ['CONTACT_ATTEMPT', 'NO_RESPONSE']));
    }
}
