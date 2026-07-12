<?php

namespace Espo\Custom\Hooks\SalesFeedback;

use Espo\Core\Hook\Hook\AfterSave;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\Repository\Option\SaveOptions;

class SalesFeedbackLearningSignalHook implements AfterSave
{
    public static int $order = 10;

    public function __construct(private EntityManager $entityManager) {}

    public function afterSave(Entity $feedback, SaveOptions $options): void
    {
        if (!$feedback->get('leadId') || !$feedback->get('feedbackType') || !$feedback->get('outcome')) {
            return;
        }
        $lead = $this->entityManager->getEntityById('Lead', $feedback->get('leadId'));
        if (!$lead) {
            return;
        }
        $signal = $this->entityManager->getRDBRepository('LearningSignal')
            ->where(['salesFeedbackId' => $feedback->getId()])
            ->findOne();
        if (!$signal) {
            $signal = $this->entityManager->getEntity('LearningSignal');
        }

        $signal->set([
            'name' => 'Learning Signal: ' . $feedback->get('feedbackType') . ' - ' . ($lead->get('name') ?: $lead->getId()),
            'leadId' => $lead->getId(),
            'salesFeedbackId' => $feedback->getId(),
            'signalType' => $feedback->get('feedbackType'),
            'predictionScore' => $lead->get('peOpportunityScoreV4'),
            'actualOutcome' => $feedback->get('outcome'),
            'product' => $feedback->get('product'),
            'campaign' => $feedback->get('campaign'),
            'assignedUserId' => $feedback->get('assignedUserId'),
        ]);
        $this->entityManager->saveEntity($signal);
    }
}
