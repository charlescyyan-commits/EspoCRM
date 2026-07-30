<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** C24 advisory commercial analysis artifact; distinct from C23 optimization insights. */
final class RevenueInsight extends Entity
{
    public const ENTITY_TYPE = 'RevenueInsight';
}
