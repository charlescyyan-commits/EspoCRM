<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Entities;

use Espo\Core\ORM\Entity;

/**
 * Append-only evidence for one governed AI provider invocation attempt.
 */
final class AIRequestLog extends Entity
{
    public const ENTITY_TYPE = 'AIRequestLog';
}
