<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/**
 * Append-only C22 execution evidence record.
 */
final class ExecutionLedger extends Entity
{
    public const ENTITY_TYPE = 'ExecutionLedger';
}
