<?php

namespace Espo\Modules\Prospecting\Classes\Select\ReplyEvent\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\ORM\Query\SelectBuilder;

class C17AwaitingReply implements Filter
{
    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where(['replyStatus' => 'SENT']);
    }
}
