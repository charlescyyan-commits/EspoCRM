<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use DateTimeInterface;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * One-way C11 read-model projection.
 *
 * C11 source records remain authoritative for human-visible lifecycle history.
 * This service only projects their accepted state to the three approved Lead
 * summary fields. It does not call providers, create work, or change source
 * records or C10 transition semantics.
 */
class EmailLifecycleProjectionService
{
    private const DRAFT_APPROVAL_STATUS_MAP = [
        'PENDING' => 'DRAFT_PENDING_APPROVAL',
        'APPROVED' => 'APPROVED',
        'REJECTED' => 'REJECTED',
    ];

    private const SEND_EXECUTION_STATUS_MAP = [
        'CREATED' => 'PENDING',
        'READY' => 'READY_TO_SEND',
        'SENT' => 'SENT',
        'FAILED' => 'FAILED',
        'CANCELLED' => 'CANCELLED',
    ];

    private const REPLY_STATUS_MAP = [
        'REPLIED' => 'REPLIED',
        'BOUNCED' => 'BOUNCED',
    ];

    private const EMAIL_EVENT_STATUS_MAP = [
        'SENT' => 'SENT',
        'DELIVERED' => 'SENT',
        'REPLIED' => 'REPLIED',
        'BOUNCED' => 'BOUNCED',
    ];

    private const EMAIL_EVENT_REPLY_STATUS_MAP = [
        'REPLIED' => 'REPLIED',
        'BOUNCED' => 'BOUNCED',
    ];

    /** @var array<string, int> */
    private const STATUS_RANK = [
        'NONE' => 0,
        'DRAFT_READY' => 10,
        'DRAFT_PENDING_APPROVAL' => 20,
        'APPROVED' => 30,
        'REJECTED' => 30,
        'PENDING' => 40,
        'READY_TO_SEND' => 50,
        'SENT' => 60,
        'FAILED' => 60,
        'CANCELLED' => 60,
        'REPLIED' => 70,
        'BOUNCED' => 70,
    ];

    public function __construct(private EntityManager $entityManager) {}

    /**
     * Project a raw EmailEvent without allowing its hook to mutate Lead state.
     *
     * EmailEvent remains the source record for legacy execution/webhook events;
     * this method preserves its status, timestamp, campaign, and reply-summary
     * behavior through the same ordered, idempotent Lead projection boundary.
     */
    public function projectEmailEvent(Entity $event): void
    {
        $eventType = $event->get('eventType');
        if (!is_string($eventType)) {
            return;
        }

        $status = self::EMAIL_EVENT_STATUS_MAP[$eventType] ?? null;
        $replyStatus = self::EMAIL_EVENT_REPLY_STATUS_MAP[$eventType] ?? null;
        if ($status === null && !in_array($eventType, ['OPENED', 'CLICKED'], true)) {
            return;
        }

        $sourceTime = $this->sourceTime($event, 'eventAt');
        $lead = $this->lead($event);
        if (!$lead || !$sourceTime || $this->isOlderThanLead($lead, $sourceTime)) {
            return;
        }

        $current = (string) ($lead->get('peEmailStatus') ?: 'NONE');
        // Preserve the legacy terminal-reply/bounce protection for later delivery events.
        if ($status === 'SENT' && in_array($current, ['REPLIED', 'BOUNCED'], true)) {
            $status = null;
        }
        if ($status !== null && $this->hasLowerRankAtSameTime($current, $status, $lead->get('peLastEmailDate'), $sourceTime)) {
            return;
        }

        $requested = [
            'peLastEmailDate' => $sourceTime,
        ];
        $campaign = $event->get('campaign');
        if (is_string($campaign) && $campaign !== '') {
            $requested['peEmailCampaignName'] = $campaign;
        }
        if ($status !== null) {
            $requested['peEmailStatus'] = $status;
        }
        if ($replyStatus !== null) {
            $requested['peEmailReplyStatus'] = $replyStatus;
        }

        $updates = $this->changedUpdates($lead, $requested);
        if ($updates) {
            $lead->set($updates);
            $this->entityManager->saveEntity($lead);
        }
    }

    public function projectDraftApproval(Entity $approval): void
    {
        $status = self::DRAFT_APPROVAL_STATUS_MAP[$approval->get('status') ?? ''] ?? null;
        if ($status === null) {
            return;
        }

        $this->projectEmailStatus($approval, $status, $this->sourceTime($approval, 'approvedAt'));
    }

    public function projectSendExecution(Entity $execution): void
    {
        $status = self::SEND_EXECUTION_STATUS_MAP[$execution->get('status') ?? ''] ?? null;
        if ($status === null) {
            return;
        }

        $this->projectEmailStatus($execution, $status, $this->sourceTime($execution));
    }

    public function projectReplyEvent(Entity $replyEvent): void
    {
        $replyStatus = self::REPLY_STATUS_MAP[$replyEvent->get('replyStatus') ?? ''] ?? 'NONE';
        $sourceTime = $this->sourceTime($replyEvent, 'receivedAt');
        $lead = $this->lead($replyEvent);
        if (!$lead || !$sourceTime || $this->isOlderThanLead($lead, $sourceTime)) {
            return;
        }

        $updates = $this->changedUpdates($lead, [
            'peEmailReplyStatus' => $replyStatus,
            'peLastEmailDate' => $sourceTime,
        ]);
        if ($updates) {
            $lead->set($updates);
            $this->entityManager->saveEntity($lead);
        }
    }

    private function projectEmailStatus(Entity $source, string $status, ?string $sourceTime): void
    {
        $lead = $this->lead($source);
        if (!$lead || !$sourceTime || $this->isOlderThanLead($lead, $sourceTime)) {
            return;
        }

        $current = (string) ($lead->get('peEmailStatus') ?: 'NONE');
        if ($this->hasLowerRankAtSameTime($current, $status, $lead->get('peLastEmailDate'), $sourceTime)) {
            return;
        }

        $updates = $this->changedUpdates($lead, [
            'peEmailStatus' => $status,
            'peLastEmailDate' => $sourceTime,
        ]);
        if ($updates) {
            $lead->set($updates);
            $this->entityManager->saveEntity($lead);
        }
    }

    private function lead(Entity $source): ?Entity
    {
        $leadId = $source->get('leadId');

        return $leadId ? $this->entityManager->getEntityById('Lead', $leadId) : null;
    }

    private function sourceTime(Entity $source, ?string $preferredField = null): ?string
    {
        $fieldNames = array_filter([$preferredField, 'modifiedAt', 'createdAt']);
        foreach ($fieldNames as $fieldName) {
            $value = $source->get($fieldName);
            if ($value instanceof DateTimeInterface) {
                return $value->format('Y-m-d H:i:s');
            }
            if (is_string($value) && $value !== '') {
                return (new DateTimeImmutable($value))->format('Y-m-d H:i:s');
            }
        }

        return null;
    }

    private function isOlderThanLead(Entity $lead, string $sourceTime): bool
    {
        $currentTime = $lead->get('peLastEmailDate');
        if (!$currentTime) {
            return false;
        }

        return new DateTimeImmutable($sourceTime) < new DateTimeImmutable((string) $currentTime);
    }

    private function hasLowerRankAtSameTime(string $current, string $next, mixed $currentTime, string $sourceTime): bool
    {
        if (!$currentTime || (new DateTimeImmutable((string) $currentTime))->format('Y-m-d H:i:s') !== $sourceTime) {
            return false;
        }

        return (self::STATUS_RANK[$next] ?? 0) < (self::STATUS_RANK[$current] ?? 0);
    }

    /** @param array<string, string> $requested */
    private function changedUpdates(Entity $lead, array $requested): array
    {
        $updates = [];
        foreach ($requested as $fieldName => $value) {
            if ((string) $lead->get($fieldName) !== $value) {
                $updates[$fieldName] = $value;
            }
        }

        return $updates;
    }
}
