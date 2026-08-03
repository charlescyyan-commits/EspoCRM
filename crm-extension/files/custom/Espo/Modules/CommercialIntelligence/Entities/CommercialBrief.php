<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP2.2 CommercialBrief — advisory commercial-intelligence artifact.
 *
 * AI content is proposal-only. Human review is final authority.
 * Not a C20 runtime surface and not a C22 execution record.
 */
final class CommercialBrief extends Entity
{
    public const ENTITY_TYPE = 'CommercialBrief';
}
