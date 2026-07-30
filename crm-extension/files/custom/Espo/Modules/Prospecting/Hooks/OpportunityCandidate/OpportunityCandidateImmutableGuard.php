<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\OpportunityCandidate;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24OpportunityCandidateSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Protects immutable candidate provenance, outcome, and audit baseline fields. */
final class OpportunityCandidateImmutableGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const ALWAYS_IMMUTABLE_FIELDS = [
        'provenanceReference',
        'outcomeReference',
        'outcomeRecordedAt',
    ];

    /** @var list<string> */
    private const LIFECYCLE_AUDIT_FIELDS = [
        'transitionHistory',
        'lastTransitionBy',
        'lastTransitionAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }
        foreach (self::ALWAYS_IMMUTABLE_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "OpportunityCandidate field {$field} is immutable."
                );
            }
        }
        foreach (self::LIFECYCLE_AUDIT_FIELDS as $field) {
            if (
                $entity->isAttributeChanged($field)
                && $options->get(
                    C24OpportunityCandidateSaveOption::LIFECYCLE_TRANSITION_AUTHORIZED
                ) !== true
            ) {
                throw new Forbidden(
                    'OpportunityCandidate lifecycle audit mutation must use its lifecycle service.'
                );
            }
        }
    }
}
