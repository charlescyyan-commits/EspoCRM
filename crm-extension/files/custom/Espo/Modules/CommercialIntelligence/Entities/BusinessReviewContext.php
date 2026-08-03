<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP3 BusinessReviewContext — composition read model for human review support.
 *
 * Holds references only. Does not own or mutate C24/C22/CRM lifecycles.
 */
final class BusinessReviewContext extends Entity
{
    public const ENTITY_TYPE = 'BusinessReviewContext';
}
