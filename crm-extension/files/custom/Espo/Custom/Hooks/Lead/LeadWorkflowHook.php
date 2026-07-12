<?php
/**
 * Phase3B02 — Lead Workflow Hook
 *
 * After-save hook that creates follow-up tasks based on Lead state changes.
 * Complements the before-save formula (state transitions) with entity creation.
 *
 * Triggers:
 *   - research_status → COMPLETED  →  creates "Prepare Outreach" task
 *   - opportunity_score >= 80       →  creates "Review and Contact Lead" task
 */

namespace Espo\Custom\Hooks\Lead;

use Espo\Core\Hook\Hook\AfterSave;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\Repository\Option\SaveOptions;

class LeadWorkflowHook implements AfterSave
{
    public static int $order = 10;

    public function __construct(private EntityManager $entityManager) {}

    public function afterSave(Entity $entity, SaveOptions $options): void
    {
        // Rule 1: Research Completed → create "Prepare Outreach" task
        if (
            $entity->isAttributeChanged('peResearchStatus') &&
            $entity->get('peResearchStatus') === 'COMPLETED'
        ) {
            $this->createTask(
                $entity,
                'Prepare Outreach for ' . ($entity->get('name') ?: 'Lead'),
                'High',
                '+1 day'
            );
        }

        // Rule 2: High Opportunity Score → create "Review and Contact Lead" task
        if (
            $entity->isAttributeChanged('peOpportunityScoreV4') &&
            ($entity->get('peOpportunityScoreV4') ?? 0) >= 80
        ) {
            $this->createTask(
                $entity,
                'Review and Contact Lead: ' . ($entity->get('name') ?: 'Lead'),
                'High',
                '+1 day'
            );
        }
    }

    private function createTask(Entity $lead, string $subject, string $priority, string $dateStart): void
    {
        $task = $this->entityManager->getEntity('Task');

        $task->set([
            'name'        => $subject,
            'parentType'  => 'Lead',
            'parentId'    => $lead->getId(),
            'assignedUserId' => $lead->get('assignedUserId'),
            'dateStart'   => date('Y-m-d', strtotime($dateStart)),
            'priority'    => $priority,
            'status'      => 'Not Started',
        ]);

        $this->entityManager->saveEntity($task);
    }
}
