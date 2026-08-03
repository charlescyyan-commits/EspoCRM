<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\CommercialBrief;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\CommercialBriefSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Protects immutable CommercialBrief proposal and provenance fields. */
final class CommercialBriefImmutabilityGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const ALWAYS_IMMUTABLE_AFTER_CREATE = [
        'name',
        'proposalContent',
        'proposalSource',
        'sourceEvidenceReference',
        'generationContext',
        'capabilityReference',
        'purposeReference',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(CommercialBriefSaveOption::PROPOSAL_CREATE_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'CommercialBrief create must use CommercialBriefProposalService.'
                );
            }

            return;
        }

        foreach (self::ALWAYS_IMMUTABLE_AFTER_CREATE as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "CommercialBrief field {$field} is immutable after create."
                );
            }
        }
    }
}
