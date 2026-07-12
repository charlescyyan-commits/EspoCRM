<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$leads = $entityManager->getRDBRepository('Lead')
    ->where(['name*' => 'PHASE3B05B-TEST%'])
    ->find();

foreach ($leads as $lead) {
    $tasks = $entityManager->getRDBRepository('Task')
        ->where(['parentType' => 'Lead', 'parentId' => $lead->getId()])
        ->find();
    foreach ($tasks as $task) {
        $entityManager->removeEntity($task);
        echo "REMOVED Task {$task->getId()}\n";
    }
    $events = $entityManager->getRDBRepository('EmailEvent')
        ->where(['leadId' => $lead->getId()])
        ->find();
    foreach ($events as $event) {
        $entityManager->removeEntity($event);
        echo "REMOVED EmailEvent {$event->getId()}\n";
    }
    $entityManager->removeEntity($lead);
    echo "REMOVED Lead {$lead->getId()}\n";
}

$user = $entityManager->getRDBRepository('User')
    ->where(['userName' => 'phase3b05b_workflow_test'])
    ->findOne();
if ($user) {
    $entityManager->removeEntity($user);
    echo "REMOVED User {$user->getId()}\n";
}

echo "PHASE3B05B_VALIDATION_CLEANUP_DONE\n";
