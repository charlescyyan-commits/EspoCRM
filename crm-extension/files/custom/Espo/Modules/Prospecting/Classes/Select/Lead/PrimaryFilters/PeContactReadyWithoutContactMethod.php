<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\Part\Condition as Cond;
use Espo\ORM\Query\SelectBuilder;

class PeContactReadyWithoutContactMethod implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder
            ->where(['outreachStatus' => 'CONTACT_READY'])
            ->where(Cond::or(
                Cond::equal(Cond::column('emailAddress'), null),
                Cond::equal(Cond::column('emailAddress'), '')
            ))
            ->where(Cond::or(
                Cond::equal(Cond::column('peContactFormUrl'), null),
                Cond::equal(Cond::column('peContactFormUrl'), '')
            ))
            ->where(Cond::or(
                Cond::equal(Cond::column('peLinkedinUrl'), null),
                Cond::equal(Cond::column('peLinkedinUrl'), '')
            ));
    }
}
