<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Exceptions\NotFound;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use stdClass;

/**
 * Dedicated ReplyEvent sync ingress (ADR-C19 / adr-c19-replyevent-v1).
 *
 * Replaces the generic connector write path progressively: connector reply
 * delivery lands here with provider facts, deduplicated on externalEventId.
 * Provider facts are written only at create; triageStatus initializes to OPEN
 * for actionable statuses through the authorized save option — the only
 * non-service triage write, and only at create time. Lead projection fields
 * stay with EmailLifecycleProjectionService; this service writes no Lead
 * fields and never mutates lifecycle state on existing records.
 */
class ReplyEventSyncService
{
    private const REPLY_STATUSES = ['SENT', 'REPLIED', 'BOUNCED', 'UNSUBSCRIBED'];

    private const PROVIDER_EVENT_MAP = [
        'email_sent' => 'SENT',
        'sent' => 'SENT',
        'email_replied' => 'REPLIED',
        'reply' => 'REPLIED',
        'email_bounced' => 'BOUNCED',
        'hard_bounce' => 'BOUNCED',
        'soft_bounce' => 'BOUNCED',
        'bounce' => 'BOUNCED',
        'email_unsubscribed' => 'UNSUBSCRIBED',
        'unsubscribed' => 'UNSUBSCRIBED',
        'SENT' => 'SENT',
        'REPLIED' => 'REPLIED',
        'BOUNCED' => 'BOUNCED',
        'UNSUBSCRIBED' => 'UNSUBSCRIBED',
    ];

    /** Actionable statuses initialize triageStatus = OPEN at ingress (ADR-C19 §3.4). */
    private const ACTIONABLE_STATUSES = ['REPLIED', 'BOUNCED', 'UNSUBSCRIBED'];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    public function sync(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->lead($payload);
        $sendExecution = $this->sendExecution($payload);
        $externalEventId = $payload['external_event_id'];
        $replyStatus = $payload['reply_status'];

        $existing = $this->entityManager->getRDBRepository('ReplyEvent')
            ->where(['externalEventId' => $externalEventId])
            ->findOne();

        if ($existing) {
            if ($existing->get('leadId') !== $lead->getId()) {
                throw new Conflict('Reply event external event ID belongs to another Lead.');
            }

            // Idempotent redelivery: provider facts are immutable after create,
            // so a duplicate returns the existing record without a second write
            // and without any lifecycle mutation.
            return [
                'success' => true,
                'accepted' => true,
                'created' => false,
                'duplicate' => true,
                'external_event_id' => $externalEventId,
                'reply_status' => $existing->get('replyStatus'),
                'reply_event_id' => $existing->getId(),
                'lead_id' => $lead->getId(),
            ];
        }

        $this->assertScope('ReplyEvent', 'create');
        if (!$this->acl->checkEntityEdit($lead)) {
            throw new Forbidden();
        }

        $event = $this->entityManager->getEntity('ReplyEvent');
        $event->set([
            'name' => $payload['name'] ?? ($replyStatus . ' - ' . $externalEventId),
            'externalEventId' => $externalEventId,
            'replyStatus' => $replyStatus,
            'receivedAt' => $this->dateTime($payload['received_at']),
            'sendTraceReference' => $payload['send_trace_reference'],
            'sendExecutionId' => $sendExecution->getId(),
            'leadId' => $lead->getId(),
            'eventMetadata' => $payload['event_metadata'] ?? null,
            'assignedUserId' => $lead->get('assignedUserId'),
        ]);

        if (in_array($replyStatus, self::ACTIONABLE_STATUSES, true)) {
            $event->set('triageStatus', ReplyTriageService::TRIAGE_OPEN);
        }

        $this->entityManager->saveEntity($event, [
            StatusMutationSaveOption::REPLY_TRIAGE_MUTATION_AUTHORIZED => true,
        ]);

        return [
            'success' => true,
            'accepted' => true,
            'created' => true,
            'duplicate' => false,
            'external_event_id' => $externalEventId,
            'reply_status' => $replyStatus,
            'triage_status' => $event->get('triageStatus'),
            'reply_event_id' => $event->getId(),
            'lead_id' => $lead->getId(),
        ];
    }

    private function payload(stdClass $body): array
    {
        $payload = json_decode(json_encode($body, JSON_THROW_ON_ERROR), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($payload)) {
            throw new BadRequest('Reply event payload must be an object.');
        }

        foreach (['external_event_id', 'reply_status', 'received_at', 'send_trace_reference', 'send_execution_id', 'lead_id'] as $field) {
            if (!is_string($payload[$field] ?? null) || trim($payload[$field]) === '') {
                throw new BadRequest("Missing reply event field: {$field}.");
            }
        }

        $normalized = self::PROVIDER_EVENT_MAP[strtolower(trim($payload['reply_status']))]
            ?? self::PROVIDER_EVENT_MAP[trim($payload['reply_status'])]
            ?? null;
        if ($normalized === null || !in_array($normalized, self::REPLY_STATUSES, true)) {
            throw new BadRequest('Unsupported reply event reply_status.');
        }
        $payload['reply_status'] = $normalized;

        foreach (['name', 'event_metadata'] as $field) {
            if (isset($payload[$field]) && !is_string($payload[$field])) {
                throw new BadRequest("Reply event field {$field} must be a string.");
            }
        }

        $this->dateTime($payload['received_at']);

        return $payload;
    }

    private function lead(array $payload): Entity
    {
        $lead = $this->entityManager->getRDBRepository('Lead')
            ->where(['id' => $payload['lead_id']])
            ->findOne();
        if (!$lead) {
            throw new NotFound('Lead was not found.');
        }
        if (!$this->acl->checkEntityRead($lead)) {
            throw new Forbidden();
        }

        return $lead;
    }

    private function sendExecution(array $payload): Entity
    {
        $sendExecution = $this->entityManager->getRDBRepository('SendExecution')
            ->where(['id' => $payload['send_execution_id']])
            ->findOne();
        if (!$sendExecution) {
            throw new NotFound('SendExecution was not found.');
        }

        return $sendExecution;
    }

    private function dateTime(string $value): string
    {
        return (new DateTimeImmutable($value))->format('Y-m-d H:i:s');
    }

    private function assertScope(string $scope, string $action): void
    {
        if (!$this->acl->check($scope, $action)) {
            throw new Forbidden();
        }
    }
}
