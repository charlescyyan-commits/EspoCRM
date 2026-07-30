<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** Immutable, advisory C24 interpretation of governed reply evidence. */
final class ReplySignal extends Entity
{
    public const ENTITY_TYPE = 'ReplySignal';
}
