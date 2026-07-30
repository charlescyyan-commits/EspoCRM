<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** C24 pre-opportunity governance artifact; not a CRM commercial record. */
final class OpportunityCandidate extends Entity
{
    public const ENTITY_TYPE = 'OpportunityCandidate';
}
