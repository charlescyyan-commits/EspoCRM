<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\HumanReviewDecisionRecord;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp4DecisionSupportSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Protects immutable HumanReviewDecisionRecord provenance fields. */
final class HumanReviewDecisionImmutabilityGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE = [
        'name',
        'decisionSupportContextReference',
        'sourceEvidenceReference',
        'capabilityReference',
        'purposeReference',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(Wp4DecisionSupportSaveOption::REVIEW_CREATE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'HumanReviewDecisionRecord create must use HumanReviewDecisionService.'
                );
            }

            return;
        }

        foreach (self::IMMUTABLE as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "HumanReviewDecisionRecord field {$field} is immutable after create."
                );
            }
        }
    }
}
