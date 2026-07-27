<?php

namespace Espo\Modules\Prospecting\Classes\Select\ReplyEvent\PrimaryFilters;

use Espo\Core\Select\Primary\Filter;
use Espo\Entities\User;
use Espo\ORM\Query\SelectBuilder;

/**
 * adr-c19-replyevent-v1: replies in progress assigned to the current user.
 * Server-side predicate; read-only queue composition.
 */
class C19MyReplies implements Filter
{
    public function __construct(private User $user) {}

    public function apply(SelectBuilder $queryBuilder): void
    {
        $queryBuilder->where([
            'triageStatus' => 'IN_PROGRESS',
            'assignedUserId' => $this->user->getId(),
        ]);
    }
}
