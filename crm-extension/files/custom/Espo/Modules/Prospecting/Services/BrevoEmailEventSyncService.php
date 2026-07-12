<?php

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
 * Append-only Brevo email execution event ingestion.
 * Does not send email. CRM lifecycle projection and Task automation are owned by EmailEventWorkflowHook.
 */
class BrevoEmailEventSyncService
{
    private const EVENT_TYPES = ['SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED'];

    private const BREVO_EVENT_MAP = [
        'email_sent' => 'SENT',
        'sent' => 'SENT',
        'email_delivered' => 'DELIVERED',
        'delivered' => 'DELIVERED',
        'email_opened' => 'OPENED',
        'opened' => 'OPENED',
        'unique_opened' => 'OPENED',
        'email_clicked' => 'CLICKED',
        'click' => 'CLICKED',
        'email_replied' => 'REPLIED',
        'reply' => 'REPLIED',
        'email_bounced' => 'BOUNCED',
        'hard_bounce' => 'BOUNCED',
        'soft_bounce' => 'BOUNCED',
        'bounce' => 'BOUNCED',
        'SENT' => 'SENT',
        'DELIVERED' => 'DELIVERED',
        'OPENED' => 'OPENED',
        'CLICKED' => 'CLICKED',
        'REPLIED' => 'REPLIED',
        'BOUNCED' => 'BOUNCED',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    public function sync(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->lead($payload);
        $externalMessageId = $payload['message_id'];
        $eventType = $payload['event_type'];

        $existing = $this->entityManager->getRDBRepository('EmailEvent')
            ->where([
                'externalMessageId' => $externalMessageId,
                'eventType' => $eventType,
            ])
            ->findOne();

        if ($existing) {
            if ($existing->get('leadId') !== $lead->getId()) {
                throw new Conflict('Email event external message ID belongs to another Lead.');
            }

            return [
                'success' => true,
                'accepted' => true,
                'created' => false,
                'duplicate' => true,
                'external_message_id' => $externalMessageId,
                'event_type' => $eventType,
                'email_event_id' => $existing->getId(),
                'lead_id' => $lead->getId(),
            ];
        }

        $this->assertScope('EmailEvent', 'create');
        if (!$this->acl->checkEntityEdit($lead)) {
            throw new Forbidden();
        }

        $event = $this->entityManager->getEntity('EmailEvent');
        $event->set([
            'name' => $eventType . ' - ' . ($payload['campaign'] ?? $externalMessageId),
            'leadId' => $lead->getId(),
            'externalMessageId' => $externalMessageId,
            'eventType' => $eventType,
            'campaign' => $payload['campaign'] ?? null,
            'eventAt' => $this->dateTime($payload['timestamp']),
            'source' => $payload['source'],
            'assignedUserId' => $lead->get('assignedUserId'),
        ]);
        $this->entityManager->saveEntity($event);

        return [
            'success' => true,
            'accepted' => true,
            'created' => true,
            'duplicate' => false,
            'external_message_id' => $externalMessageId,
            'event_type' => $eventType,
            'email_event_id' => $event->getId(),
            'lead_id' => $lead->getId(),
        ];
    }

    private function payload(stdClass $body): array
    {
        $payload = json_decode(json_encode($body, JSON_THROW_ON_ERROR), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($payload)) {
            throw new BadRequest('Brevo email event payload must be an object.');
        }

        foreach (['lead_id', 'message_id', 'event_type', 'timestamp'] as $field) {
            if (!is_string($payload[$field] ?? null) || trim($payload[$field]) === '') {
                throw new BadRequest("Missing email event field: {$field}.");
            }
        }

        $normalized = self::BREVO_EVENT_MAP[strtolower(trim($payload['event_type']))]
            ?? self::BREVO_EVENT_MAP[trim($payload['event_type'])]
            ?? null;
        if ($normalized === null || !in_array($normalized, self::EVENT_TYPES, true)) {
            throw new BadRequest('Unsupported Brevo event_type.');
        }
        $payload['event_type'] = $normalized;

        foreach (['campaign', 'external_lead_id', 'reply_status'] as $field) {
            if (isset($payload[$field]) && !is_string($payload[$field])) {
                throw new BadRequest("Email event field {$field} must be a string.");
            }
        }

        $source = $payload['source'] ?? 'BREVO';
        if (!is_string($source) || !in_array($source, ['BREVO', 'CONNECTOR_SYNC', 'MANUAL'], true)) {
            throw new BadRequest('Unsupported email event source.');
        }
        $payload['source'] = $source;
        $this->dateTime($payload['timestamp']);

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
        if (isset($payload['external_lead_id']) && $payload['external_lead_id'] !== $lead->get('peCandidateId')) {
            throw new Conflict('external_lead_id does not match the Lead.');
        }

        return $lead;
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
