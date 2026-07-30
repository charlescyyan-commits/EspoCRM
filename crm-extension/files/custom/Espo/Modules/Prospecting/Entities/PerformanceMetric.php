<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** Immutable C23 point-in-time aggregate analytical measurement. */
final class PerformanceMetric extends Entity
{
    public const ENTITY_TYPE = 'PerformanceMetric';
}
