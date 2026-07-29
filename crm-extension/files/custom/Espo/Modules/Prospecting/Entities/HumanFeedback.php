<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/**
 * Append-only human review signal about C21 intelligence.
 */
final class HumanFeedback extends Entity
{
    public const ENTITY_TYPE = 'HumanFeedback';
}
