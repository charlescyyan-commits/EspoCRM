<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\SendExecution;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\SendExecutionTransitionService;
use Espo\Modules\Prospecting\Services\StatusMutationSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Terminal persistence boundary for SendExecution lifecycle fields.
 *
 * Ownership follows ADR-C18 / adr-c18-sendexecution-v1: only
 * SendExecutionTransitionService may mutate status / sentAt. sendRequestId is
 * create-time evidence and immutable thereafter. Provider-trace fields and
 * ordinary record attributes remain writable via normal CRUD.
 *
 * Authorization for transitions remains on the transition service (edit ACL +
 * workflow action keys), matching the WorkflowAuthorizationService ownership
 * pattern without introducing a second ACL architecture.
 */
class SendExecutionStatusMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    /** Lifecycle fields owned by SendExecutionTransitionService. */
    private const LIFECYCLE_FIELDS = ['status', 'sentAt'];

    /**
     * Terminal audit / idempotency evidence.
     * sentAt is transition-owned; sendRequestId is create-only.
     */
    private const TERMINAL_EVIDENCE_FIELDS = ['sentAt', 'sendRequestId'];

    private const TERMINAL_STATUSES = [
        SendExecutionTransitionService::STATUS_SENT,
        SendExecutionTransitionService::STATUS_CANCELLED,
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        $authorized = $options->get(
            StatusMutationSaveOption::SEND_EXECUTION_STATUS_MUTATION_AUTHORIZED
        ) === true;

        if ($entity->isNew()) {
            $this->assertAuthorizedCreate($entity);

            return;
        }

        if ($entity->isAttributeChanged('sendRequestId')) {
            throw new Forbidden(
                'SendExecution sendRequestId is immutable after create.'
            );
        }

        if (!$this->hasChangedAttributes($entity, self::LIFECYCLE_FIELDS)) {
            // Provider-trace fields and ordinary CRUD attributes remain writable.
            return;
        }

        if ($authorized) {
            return;
        }

        $fetchedStatus = (string) ($entity->getFetched('status') ?: '');
        if (in_array($fetchedStatus, self::TERMINAL_STATUSES, true)) {
            throw new Forbidden(
                'SendExecution terminal lifecycle fields are immutable outside SendExecutionTransitionService.'
            );
        }

        throw new Forbidden(
            'SendExecution status mutation must use SendExecutionTransitionService.'
        );
    }

    private function assertAuthorizedCreate(Entity $entity): void
    {
        $status = (string) ($entity->get('status') ?: SendExecutionTransitionService::STATUS_CREATED);
        if ($status !== SendExecutionTransitionService::STATUS_CREATED) {
            throw new Forbidden(
                'SendExecution status mutation must use SendExecutionTransitionService.'
            );
        }

        foreach (self::TERMINAL_EVIDENCE_FIELDS as $field) {
            if ($field === 'sendRequestId') {
                // Create-time assignment is required idempotency evidence.
                continue;
            }
            $value = $entity->get($field);
            if ($value !== null && $value !== '') {
                throw new Forbidden(
                    'SendExecution sentAt may only be written by SendExecutionTransitionService.'
                );
            }
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
