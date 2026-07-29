<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/**
 * Human authorization record for one proposed C22 execution action.
 */
final class ActionGate extends Entity
{
    public const ENTITY_TYPE = 'ActionGate';
}
