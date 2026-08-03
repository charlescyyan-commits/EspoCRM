<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\BusinessReviewContext;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp3InsightSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Guards BusinessReviewContext create/close save options. */
final class BusinessReviewContextGuard implements BeforeSave
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(Wp3InsightSaveOption::REVIEW_CONTEXT_CREATE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'BusinessReviewContext create must use BusinessReviewContextAggregationService.'
                );
            }
            $status = (string) $entity->get('status');
            if ($status !== '' && $status !== 'OPEN') {
                throw new Forbidden('BusinessReviewContext may only be created OPEN.');
            }

            return;
        }

        if ($entity->isAttributeChanged('status')) {
            if (
                $options->get(Wp3InsightSaveOption::REVIEW_CONTEXT_CLOSE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'BusinessReviewContext status mutation must use AggregationService::close.'
                );
            }
            $from = (string) $entity->getFetched('status');
            $to = (string) $entity->get('status');
            if (!($from === 'OPEN' && $to === 'CLOSED')) {
                throw new Forbidden(
                    "BusinessReviewContext transition {$from} to {$to} is forbidden."
                );
            }
        }

        foreach ([
            'commercialBriefReferences',
            'commercialInsightReferences',
            'opportunityCandidateReference',
            'revenueInsightReference',
            'pipelineMetricReference',
            'aggregationSnapshot',
            'capabilityReference',
            'purposeReference',
            'name',
        ] as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "BusinessReviewContext field {$field} is immutable after create."
                );
            }
        }
    }
}
