<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\RevenueInsight;

use DateTimeImmutable;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\C24RevenueInsightSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/** Validates future human RevenueInsight lifecycle transition requests only. */
final class RevenueInsightLifecycleGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'GENERATED' => ['REVIEWED'],
        'REVIEWED' => ['ACCEPTED', 'REJECTED'],
        'ACCEPTED' => [],
        'REJECTED' => [],
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew() || !$entity->isAttributeChanged('reviewStatus')) {
            return;
        }
        if ($options->get(
            C24RevenueInsightSaveOption::LIFECYCLE_TRANSITION_AUTHORIZED
        ) !== true) {
            throw new Forbidden(
                'RevenueInsight transition requires authorized lifecycle context.'
            );
        }

        $from = (string) $entity->getFetched('reviewStatus');
        $to = (string) $entity->get('reviewStatus');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "RevenueInsight transition {$from} to {$to} is forbidden."
            );
        }
        $this->requiredText(
            $options->get(C24RevenueInsightSaveOption::LIFECYCLE_ACTOR_REFERENCE),
            'authenticated actor'
        );
        $this->requiredText(
            $options->get(C24RevenueInsightSaveOption::LIFECYCLE_TRANSITION_REASON),
            'transition reason'
        );
        $this->requiredTimestamp(
            $options->get(C24RevenueInsightSaveOption::LIFECYCLE_TRANSITION_TIMESTAMP)
        );
    }

    private function requiredText(mixed $value, string $label): void
    {
        if (!is_string($value) || trim($value) === '') {
            throw new Forbidden("RevenueInsight transition requires {$label}.");
        }
    }

    private function requiredTimestamp(mixed $value): void
    {
        if (!is_string($value) || trim($value) === '') {
            throw new Forbidden('RevenueInsight transition requires timestamp.');
        }
        try {
            new DateTimeImmutable($value);
        } catch (\Exception) {
            throw new Forbidden('RevenueInsight transition requires timestamp.');
        }
    }
}
