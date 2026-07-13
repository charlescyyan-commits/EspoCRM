<?php
/**
 * Phase3B06 — Remove synthetic workspace verification records and disposable users.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$em = $app->getContainer()->get('entityManager');

$leads = $em->getRDBRepository('Lead')
    ->where(['name*' => 'PHASE3B06-TEST%'])
    ->find();

foreach ($leads as $lead) {
    $leadId = $lead->getId();

    foreach ($em->getRDBRepository('LearningSignal')->where(['leadId' => $leadId])->find() as $signal) {
        $em->removeEntity($signal);
        echo "REMOVED LearningSignal {$signal->getId()}\n";
    }
    foreach ($em->getRDBRepository('SalesFeedback')->where(['leadId' => $leadId])->find() as $feedback) {
        $em->removeEntity($feedback);
        echo "REMOVED SalesFeedback {$feedback->getId()}\n";
    }
    foreach ($em->getRDBRepository('EmailEvent')->where(['leadId' => $leadId])->find() as $event) {
        $em->removeEntity($event);
        echo "REMOVED EmailEvent {$event->getId()}\n";
    }
    foreach ($em->getRDBRepository('ResearchEvidence')->where(['leadId' => $leadId])->find() as $evidence) {
        $em->removeEntity($evidence);
        echo "REMOVED ResearchEvidence {$evidence->getId()}\n";
    }
    foreach ($em->getRDBRepository('Task')->where(['parentType' => 'Lead', 'parentId' => $leadId])->find() as $task) {
        $em->removeEntity($task);
        echo "REMOVED Task {$task->getId()}\n";
    }

    $em->removeEntity($lead);
    echo "REMOVED Lead {$leadId}\n";
}

foreach (['research_test'] as $userName) {
    $user = $em->getRDBRepository('User')->where(['userName' => $userName])->findOne();
    if ($user) {
        $em->removeEntity($user);
        echo "REMOVED User {$user->getId()} {$userName}\n";
    }
}

echo "PHASE3B06_VALIDATION_CLEANUP_DONE\n";
