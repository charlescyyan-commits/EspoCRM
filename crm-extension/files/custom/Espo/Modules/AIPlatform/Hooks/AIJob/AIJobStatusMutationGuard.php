<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Hooks\AIJob;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\AIPlatform\Services\AIJobService;
use Espo\Modules\AIPlatform\Services\AIJobStatusMutationSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for AIJob lifecycle and retry facts.
 *
 * AIJobService is the sole lifecycle writer. This hook does not execute work,
 * schedule a retry, or contact an external system.
 */
final class AIJobStatusMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const SERVICE_OWNED_FIELDS = [
        'status',
        'attemptCount',
        'failureCategory',
        'lastError',
        'nextRetryAt',
        'startedAt',
        'completedAt',
    ];

    /** @var list<string> */
    private const CREATE_TIME_SERVICE_FIELDS = [
        'failureCategory',
        'lastError',
        'nextRetryAt',
        'startedAt',
        'completedAt',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        $authorized = $options->get(
            AIJobStatusMutationSaveOption::AI_JOB_STATUS_MUTATION_AUTHORIZED
        ) === true;

        if ($entity->isNew()) {
            $this->assertValidCreateState($entity, $authorized);

            return;
        }

        if (!$this->hasChangedAttributes($entity, self::SERVICE_OWNED_FIELDS)) {
            return;
        }

        if ($authorized) {
            return;
        }

        throw new Forbidden('AIJob lifecycle fields may only be written by AIJobService.');
    }

    private function assertValidCreateState(Entity $entity, bool $authorized): void
    {
        $status = (string) ($entity->get('status') ?: AIJobService::STATUS_QUEUED);
        $attemptCount = (int) ($entity->get('attemptCount') ?? 0);
        if ($status !== AIJobService::STATUS_QUEUED || $attemptCount !== 0) {
            throw new Forbidden('AIJob creation must initialize to QUEUED with zero attempts.');
        }

        foreach (self::CREATE_TIME_SERVICE_FIELDS as $field) {
            $value = $entity->get($field);
            if ($value !== null && $value !== '') {
                throw new Forbidden('AIJob lifecycle evidence may only be written by AIJobService.');
            }
        }

        if (!$authorized && $entity->isAttributeChanged('status')) {
            throw new Forbidden('AIJob status mutation must use AIJobService.');
        }
    }

    /**
     * @param list<string> $fields
     */
    private function hasChangedAttributes(Entity $entity, array $fields): bool
    {
        foreach ($fields as $field) {
            if ($entity->isAttributeChanged($field)) {
                return true;
            }
        }

        return false;
    }
}
