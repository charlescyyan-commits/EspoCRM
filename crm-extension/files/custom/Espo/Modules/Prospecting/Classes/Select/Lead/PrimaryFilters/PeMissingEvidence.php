<?php

namespace Espo\Modules\Prospecting\Classes\Select\Lead\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Name\Attribute;
use Espo\ORM\Query\SelectBuilder;

class PeMissingEvidence implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder
            ->distinct()
            ->leftJoin('ResearchEvidence', 'researchEvidence', [
                'leadId:' => Attribute::ID,
                Attribute::DELETED => false,
            ])
            ->where([
                'peResearchStatus' => 'COMPLETED',
                'researchEvidence.id' => null,
            ]);
    }
}
