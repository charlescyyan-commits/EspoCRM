<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP4 HumanReviewDecisionRecord — human review outcome only.
 *
 * Not a persisted decision-intent store (ADR-C25-004 §7.1).
 * Does not enact CRM/C22/C24 transitions.
 */
final class HumanReviewDecisionRecord extends Entity
{
    public const ENTITY_TYPE = 'HumanReviewDecisionRecord';
}
