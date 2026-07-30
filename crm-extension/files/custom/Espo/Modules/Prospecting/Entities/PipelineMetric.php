<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Entities;

use Espo\Core\ORM\Entity;

/** C24 commercial pipeline measurement artifact; distinct from C23 acquisition metrics. */
final class PipelineMetric extends Entity
{
    public const ENTITY_TYPE = 'PipelineMetric';
}
