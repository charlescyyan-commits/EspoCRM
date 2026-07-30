<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\PipelineMetric;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24PipelineMetricSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Blocks silent modification of published commercial metric definitions. */
final class PipelineMetricIntegrityGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const PROTECTED_FIELDS = [
        'metricType',
        'methodology',
        'provenance',
        'reportingPeriod',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }
        foreach (self::PROTECTED_FIELDS as $field) {
            if (
                $entity->isAttributeChanged($field)
                && $options->get(
                    C24PipelineMetricSaveOption::INTEGRITY_UPDATE_AUTHORIZED
                ) !== true
            ) {
                throw new Forbidden(
                    "PipelineMetric field {$field} requires authorized integrity context."
                );
            }
        }
    }
}
