<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** Aggregate, advisory-only C23 operational optimization record. */
final class OptimizationInsight extends Entity
{
    public const ENTITY_TYPE = 'OptimizationInsight';
}
