<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\CommercialInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Services\Wp3InsightSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Enforces CommercialInsight reviewStatus transitions. */
final class CommercialInsightReviewStatusGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'GENERATED' => ['REVIEWED'],
        'REVIEWED' => ['ACCEPTED', 'DISMISSED'],
        'ACCEPTED' => [],
        'DISMISSED' => [],
    ];

    /** @var list<string> */
    private const LIFECYCLE_FIELDS = [
        'reviewStatus',
        'transitionHistory',
        'lastTransitionBy',
        'lastTransitionAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            $status = (string) $entity->get('reviewStatus');
            if ($status !== '' && $status !== 'GENERATED') {
                throw new Forbidden(
                    'CommercialInsight may only be created in GENERATED status.'
                );
            }

            return;
        }

        $hasLifecycleMutation = false;
        foreach (self::LIFECYCLE_FIELDS as $field) {
            $hasLifecycleMutation = $hasLifecycleMutation
                || $entity->isAttributeChanged($field);
        }
        if (!$hasLifecycleMutation) {
            return;
        }
        if (
            $options->get(Wp3InsightSaveOption::INSIGHT_REVIEW_TRANSITION_AUTHORIZED)
            !== true
        ) {
            throw new Forbidden(
                'CommercialInsight review mutation must use CommercialInsightReviewService.'
            );
        }

        $from = (string) $entity->getFetched('reviewStatus');
        $to = (string) $entity->get('reviewStatus');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "CommercialInsight transition {$from} to {$to} is forbidden."
            );
        }
    }
}
