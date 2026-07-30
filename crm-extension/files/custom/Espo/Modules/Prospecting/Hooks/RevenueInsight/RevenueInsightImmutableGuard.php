<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\RevenueInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24RevenueInsightSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Preserves immutable commercial-analysis source and reporting evidence. */
final class RevenueInsightImmutableGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_FIELDS = [
        'sourceReference',
        'provenance',
        'metricReferences',
        'reportingPeriod',
        'createdAt',
        'createdBy',
    ];

    /** @var list<string> */
    private const LIFECYCLE_FIELDS = [
        'reviewStatus',
        'reviewNote',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }
        foreach (self::IMMUTABLE_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden("RevenueInsight field {$field} is immutable.");
            }
        }
        foreach (self::LIFECYCLE_FIELDS as $field) {
            if (
                $entity->isAttributeChanged($field)
                && $options->get(
                    C24RevenueInsightSaveOption::LIFECYCLE_TRANSITION_AUTHORIZED
                ) !== true
            ) {
                throw new Forbidden(
                    'RevenueInsight lifecycle mutation requires authorized context.'
                );
            }
        }
    }
}
