<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\DecisionSupportContext;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp4DecisionSupportSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Guards DecisionSupportContext create/close save options. */
final class DecisionSupportContextGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var list<string> */
    private const IMMUTABLE_AFTER_CREATE = [
        'name',
        'commercialBriefReferences',
        'commercialInsightReferences',
        'businessReviewContextReferences',
        'opportunityCandidateReference',
        'revenueInsightReference',
        'pipelineMetricReference',
        'aggregationSnapshot',
        'sourceEvidenceReference',
        'capabilityReference',
        'purposeReference',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(Wp4DecisionSupportSaveOption::CONTEXT_CREATE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'DecisionSupportContext create must use DecisionSupportContextAggregationService.'
                );
            }
            if ((string) $entity->get('status') !== 'OPEN') {
                throw new Forbidden('DecisionSupportContext may only be created OPEN.');
            }

            return;
        }

        if ($entity->isAttributeChanged('status')) {
            if (
                $options->get(Wp4DecisionSupportSaveOption::CONTEXT_CLOSE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'DecisionSupportContext status mutation must use AggregationService::close.'
                );
            }
            $from = (string) $entity->getFetched('status');
            $to = (string) $entity->get('status');
            if (!($from === 'OPEN' && $to === 'CLOSED')) {
                throw new Forbidden(
                    "DecisionSupportContext transition {$from} to {$to} is forbidden."
                );
            }
        }

        foreach (self::IMMUTABLE_AFTER_CREATE as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "DecisionSupportContext field {$field} is immutable after create."
                );
            }
        }
    }
}
