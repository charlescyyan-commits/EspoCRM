<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\ReplyEvent;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\ReplyTriageService;
use Espo\Modules\Prospecting\Services\StatusMutationSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Terminal persistence boundary for ReplyEvent (ADR-C19 / adr-c19-replyevent-v1).
 *
 * Provider facts (replyStatus, externalEventId, receivedAt) are create-time
 * sync-ingress facts and immutable afterwards — a contradicting provider event
 * is a new ReplyEvent with a new externalEventId. Triage fields are owned by
 * ReplyTriageService and accepted only with the authorized save option; sync
 * ingress uses the same option for create-time triage initialization.
 *
 * Authorization for transitions remains on the triage service (edit ACL +
 * workflow action keys), matching the WorkflowAuthorizationService ownership
 * pattern without introducing a second ACL architecture.
 */
class ReplyEventMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    /** Provider facts owned by sync ingress (PostSyncReplyEvent) at create time. */
    private const PROVIDER_FACT_FIELDS = ['replyStatus', 'externalEventId', 'receivedAt'];

    /** Lifecycle fields owned by ReplyTriageService. */
    private const TRIAGE_FIELDS = ['triageStatus', 'closedReason', 'closedAt', 'closedById'];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        $triageAuthorized = $options->get(
            StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED
        ) === true;

        if ($entity->isNew()) {
            $this->assertAuthorizedCreateInitialization($entity, $triageAuthorized);

            return;
        }

        if ($this->hasChangedAttributes($entity, self::PROVIDER_FACT_FIELDS)) {
            throw new Forbidden(
                'ReplyEvent provider facts are immutable after create; only sync ingress may write them.'
            );
        }

        if (!$this->hasChangedAttributes($entity, self::TRIAGE_FIELDS)) {
            // Ordinary record attributes remain writable.
            return;
        }

        if ($triageAuthorized) {
            return;
        }

        throw new Forbidden(
            'ReplyEvent triage fields may only be written by ReplyTriageService.'
        );
    }

    private function assertAuthorizedCreateInitialization(Entity $entity, bool $triageAuthorized): void
    {
        $triageStatus = $entity->get('triageStatus');
        $hasTriageStatus = is_string($triageStatus) && $triageStatus !== '';
        $hasClosedAudit = $this->hasClosedAuditValues($entity);

        if (!$hasTriageStatus && !$hasClosedAudit) {
            // Plain create without triage state stays valid while the generic
            // connector write path migrates to PostSyncReplyEvent progressively.
            return;
        }

        if (!$triageAuthorized) {
            throw new Forbidden(
                'ReplyEvent triage initialization at create requires the authorized sync ingress save option.'
            );
        }

        if ($triageStatus !== ReplyTriageService::TRIAGE_OPEN || $hasClosedAudit) {
            throw new Forbidden(
                'ReplyEvent triage may only initialize to OPEN at create; closed audit fields are transition-owned.'
            );
        }
    }

    private function hasClosedAuditValues(Entity $entity): bool
    {
        foreach (['closedReason', 'closedAt', 'closedById'] as $field) {
            $value = $entity->get($field);
            if ($value !== null && $value !== '') {
                return true;
            }
        }

        return false;
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
