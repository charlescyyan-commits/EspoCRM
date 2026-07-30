<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\OptimizationInsight;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C23OptimizationInsightLifecycleSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Enforces closed human-review transitions while preserving insight content. */
final class OptimizationInsightLifecycleGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var list<string> */
    private const CONTENT_FIELDS = [
        'name',
        'insightType',
        'title',
        'description',
        'recommendation',
        'evidenceReference',
        'sourcePeriodStart',
        'sourcePeriodEnd',
        'generatedAt',
        'freshnessStatus',
        'confidence',
        'supersedesInsightId',
        'createdAt',
    ];

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'GENERATED' => ['REVIEWED'],
        'REVIEWED' => ['ACCEPTED', 'REJECTED'],
        'ACCEPTED' => [],
        'REJECTED' => [],
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }
        if (
            $options->get(
                C23OptimizationInsightLifecycleSaveOption::LIFECYCLE_MUTATION_AUTHORIZED
            ) !== true
        ) {
            return;
        }

        foreach (self::CONTENT_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "OptimizationInsight content field {$field} is immutable."
                );
            }
        }
        if (!$entity->isAttributeChanged('status')) {
            throw new Forbidden(
                'OptimizationInsight lifecycle mutation requires a status transition.'
            );
        }

        $from = (string) $entity->getFetched('status');
        $to = (string) $entity->get('status');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "OptimizationInsight transition {$from} to {$to} is forbidden."
            );
        }
        if (
            trim((string) $entity->get('reviewedAt')) === ''
            || trim((string) $entity->get('reviewedByReference')) === ''
        ) {
            throw new Forbidden(
                'OptimizationInsight lifecycle transition requires review provenance.'
            );
        }
        if (
            $to === 'REJECTED'
            && trim((string) $entity->get('decisionNote')) === ''
        ) {
            throw new Forbidden(
                'Rejected OptimizationInsight requires a decisionNote.'
            );
        }
    }
}
