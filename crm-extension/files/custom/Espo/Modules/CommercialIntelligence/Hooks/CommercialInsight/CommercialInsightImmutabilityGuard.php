<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\CommercialInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp3InsightSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Protects immutable CommercialInsight advisory and provenance fields. */
final class CommercialInsightImmutabilityGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_AFTER_CREATE = [
        'name',
        'advisoryContent',
        'advisorySource',
        'sourceEvidenceReference',
        'commercialBriefReference',
        'opportunityCandidateReference',
        'revenueInsightReference',
        'pipelineMetricReference',
        'capabilityReference',
        'purposeReference',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(Wp3InsightSaveOption::INSIGHT_CREATE_AUTHORIZED) !== true
            ) {
                throw new Forbidden(
                    'CommercialInsight create must use CommercialInsightProposalService.'
                );
            }

            return;
        }

        foreach (self::IMMUTABLE_AFTER_CREATE as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "CommercialInsight field {$field} is immutable after create."
                );
            }
        }
    }
}
