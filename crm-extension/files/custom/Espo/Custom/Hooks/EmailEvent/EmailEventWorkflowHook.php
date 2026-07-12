<?php
/**
 * Phase3B05-B — EmailEvent Workflow Hook
 *
 * After-save CRM lifecycle for Brevo execution events.
 * Does not send email. Does not alter EmailEvent contract fields.
 *
 * Rules:
 *   SENT     → Lead peEmailStatus=SENT, peLastEmailDate
 *   REPLIED  → Lead peEmailStatus/peEmailReplyStatus=REPLIED + Task "Follow up customer reply"
 *   BOUNCED  → Lead peEmailStatus=BOUNCED + Task "Verify customer email"
 *   OPENED   → record only (no sales-status change); may refresh peLastEmailDate
 *   DELIVERED/CLICKED → engagement timestamps only; DELIVERED may keep peEmailStatus=SENT
 */

namespace Espo\Custom\Hooks\EmailEvent;

use Espo\Core\Hook\Hook\AfterSave;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\Repository\Option\SaveOptions;

class EmailEventWorkflowHook implements AfterSave
{
    public static int $order = 20;

    private const REPLY_TASK = 'Follow up customer reply';
    private const BOUNCE_TASK = 'Verify customer email';

    public function __construct(private EntityManager $entityManager) {}

    public function afterSave(Entity $event, SaveOptions $options): void
    {
        if (!$event->isNew()) {
            return;
        }

        $leadId = $event->get('leadId');
        $eventType = $event->get('eventType');
        if (!$leadId || !$eventType) {
            return;
        }

        $lead = $this->entityManager->getEntityById('Lead', $leadId);
        if (!$lead) {
            return;
        }

        match ($eventType) {
            'SENT' => $this->applySent($lead, $event),
            'DELIVERED' => $this->applyDelivered($lead, $event),
            'OPENED', 'CLICKED' => $this->applyEngagementOnly($lead, $event),
            'REPLIED' => $this->applyReplied($lead, $event),
            'BOUNCED' => $this->applyBounced($lead, $event),
            default => null,
        };
    }

    private function applySent(Entity $lead, Entity $event): void
    {
        $current = (string) ($lead->get('peEmailStatus') ?: 'NONE');
        $updates = $this->timestampUpdates($event);
        if (!in_array($current, ['REPLIED', 'BOUNCED'], true)) {
            $updates['peEmailStatus'] = 'SENT';
        }
        $this->saveLead($lead, $updates);
    }

    private function applyDelivered(Entity $lead, Entity $event): void
    {
        // Delivery confirms send execution; coarse Lead enum stays SENT (no DELIVERED option).
        $current = (string) ($lead->get('peEmailStatus') ?: 'NONE');
        $updates = $this->timestampUpdates($event);
        if (!in_array($current, ['REPLIED', 'BOUNCED'], true)) {
            $updates['peEmailStatus'] = 'SENT';
        }
        $this->saveLead($lead, $updates);
    }

    private function applyEngagementOnly(Entity $lead, Entity $event): void
    {
        // Rule 4: record engagement; do not change sales peEmailStatus.
        $this->saveLead($lead, $this->timestampUpdates($event));
    }

    private function applyReplied(Entity $lead, Entity $event): void
    {
        $updates = $this->timestampUpdates($event);
        $updates['peEmailStatus'] = 'REPLIED';
        $updates['peEmailReplyStatus'] = 'REPLIED';
        $this->saveLead($lead, $updates);
        $this->createTaskOnce(
            $lead,
            self::REPLY_TASK,
            'High',
            '+1 day',
            'Customer replied to outreach. Follow up from CRM.'
        );
    }

    private function applyBounced(Entity $lead, Entity $event): void
    {
        $updates = $this->timestampUpdates($event);
        $updates['peEmailStatus'] = 'BOUNCED';
        $updates['peEmailReplyStatus'] = 'BOUNCED';
        $this->saveLead($lead, $updates);
        $this->createTaskOnce(
            $lead,
            self::BOUNCE_TASK,
            'High',
            '+1 day',
            'Outbound email bounced. Verify customer email validity.'
        );
    }

    private function timestampUpdates(Entity $event): array
    {
        $updates = [];
        if ($event->get('eventAt')) {
            $updates['peLastEmailDate'] = $event->get('eventAt');
        }
        if ($event->get('campaign')) {
            $updates['peEmailCampaignName'] = $event->get('campaign');
        }

        return $updates;
    }

    private function saveLead(Entity $lead, array $updates): void
    {
        if (!$updates) {
            return;
        }
        $lead->set($updates);
        $this->entityManager->saveEntity($lead);
    }

    private function createTaskOnce(
        Entity $lead,
        string $subject,
        string $priority,
        string $dateStart,
        string $description
    ): void {
        $existing = $this->entityManager->getRDBRepository('Task')
            ->where([
                'parentType' => 'Lead',
                'parentId' => $lead->getId(),
                'name' => $subject,
                'status!=' => 'Completed',
            ])
            ->findOne();
        if ($existing) {
            return;
        }

        $task = $this->entityManager->getEntity('Task');
        $task->set([
            'name' => $subject,
            'description' => $description,
            'parentType' => 'Lead',
            'parentId' => $lead->getId(),
            'assignedUserId' => $lead->get('assignedUserId'),
            'dateStart' => date('Y-m-d', strtotime($dateStart)),
            'priority' => $priority,
            'status' => 'Not Started',
        ]);
        $this->entityManager->saveEntity($task);
    }
}
