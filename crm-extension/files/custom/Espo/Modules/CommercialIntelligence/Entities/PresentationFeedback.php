<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP4 PresentationFeedback — human presentation / explanation feedback.
 *
 * Human governance signal only. Not a training loop or shadow CRM store.
 */
final class PresentationFeedback extends Entity
{
    public const ENTITY_TYPE = 'PresentationFeedback';
}
