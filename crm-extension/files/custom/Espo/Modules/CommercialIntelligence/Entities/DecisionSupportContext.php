<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP4 DecisionSupportContext — human decision preparation composition.
 *
 * Commercial Decision Support Layer / Human Decision Workspace.
 * References only; does not own C24/C22/CRM lifecycles.
 */
final class DecisionSupportContext extends Entity
{
    public const ENTITY_TYPE = 'DecisionSupportContext';
}
