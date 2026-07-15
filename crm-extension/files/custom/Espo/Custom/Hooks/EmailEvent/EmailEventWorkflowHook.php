<?php
/**
 * Phase3B05-B EmailEvent Workflow Hook.
 *
 * Lead email lifecycle summaries are projected only by
 * EmailLifecycleProjectionService. This hook retains the legacy CRM Task
 * side effects for reply and bounce events; it never writes Lead state.
 */

namespace Espo\Custom\Hooks\EmailEvent;

use Espo\Core\Hook\Hook\AfterSave;
use Espo\Modules\Prospecting\Services\EmailLifecycleProjectionService;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\Repository\Option\SaveOptions;

class EmailEventWorkflowHook implements AfterSave
{
    public static int $order = 20;

    private const REPLY_TASK = 'Follow up customer reply';
    private const BOUNCE_TASK = 'Verify customer email';

    public function __construct(
        private EntityManager $entityManager,
        private EmailLifecycleProjectionService $projectionService,
    ) {}

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

        $this->projectionService->projectEmailEvent($event);

        if (!in_array($eventType, ['REPLIED', 'BOUNCED'], true)) {
            return;
        }

        $lead = $this->entityManager->getEntityById('Lead', $leadId);
        if (!$lead) {
            return;
        }

        match ($eventType) {
            'REPLIED' => $this->createTaskOnce(
                $lead,
                self::REPLY_TASK,
                'High',
                '+1 day',
                'Customer replied to outreach. Follow up from CRM.'
            ),
            'BOUNCED' => $this->createTaskOnce(
                $lead,
                self::BOUNCE_TASK,
                'High',
                '+1 day',
                'Outbound email bounced. Verify customer email validity.'
            ),
        };
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
