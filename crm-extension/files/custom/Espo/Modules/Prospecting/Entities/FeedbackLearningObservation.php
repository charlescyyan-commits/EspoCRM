<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** Immutable C23 aggregate learning observation for human consideration. */
final class FeedbackLearningObservation extends Entity
{
    public const ENTITY_TYPE = 'FeedbackLearningObservation';
}
