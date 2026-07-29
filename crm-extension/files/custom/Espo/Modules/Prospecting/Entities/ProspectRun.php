<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/**
 * Bounded C22 execution batch container with no reasoning authority.
 */
final class ProspectRun extends Entity
{
    public const ENTITY_TYPE = 'ProspectRun';
}
