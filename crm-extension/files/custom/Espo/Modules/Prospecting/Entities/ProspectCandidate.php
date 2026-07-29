<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/**
 * C22 execution identity; never a CRM Lead or lifecycle owner.
 */
final class ProspectCandidate extends Entity
{
    public const ENTITY_TYPE = 'ProspectCandidate';
}
