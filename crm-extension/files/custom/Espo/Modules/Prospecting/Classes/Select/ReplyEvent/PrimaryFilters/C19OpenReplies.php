<?php

namespace Espo\Modules\Prospecting\Classes\Select\ReplyEvent\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

/**
 * adr-c19-replyevent-v1: actionable replies awaiting triage ownership.
 * Single server-side predicate; read-only queue composition.
 */
class C19OpenReplies implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['triageStatus' => 'OPEN']);
    }
}
