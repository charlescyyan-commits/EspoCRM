<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP3 CommercialInsight — advisory commercial-intelligence support artifact.
 *
 * Revenue Analyst Assistant content is proposal-only.
 * Not a C20 runtime surface, C22 execution record, or C24 entity replacement.
 */
final class CommercialInsight extends Entity
{
    public const ENTITY_TYPE = 'CommercialInsight';
}
