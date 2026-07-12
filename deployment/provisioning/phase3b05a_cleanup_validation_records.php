<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$leads = $entityManager->getRDBRepository('Lead')
    ->where(['name*' => 'PHASE3B05A-TEST%'])
    ->find();

foreach ($leads as $lead) {
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

$orphanEvents = $entityManager->getRDBRepository('EmailEvent')
    ->where(['externalMessageId*' => 'PHASE3B05A%'])
    ->find();
foreach ($orphanEvents as $event) {
    $entityManager->removeEntity($event);
    echo "REMOVED EmailEvent {$event->getId()}\n";
}

$user = $entityManager->getRDBRepository('User')
    ->where(['userName' => 'phase3b05a_brevo_test'])
    ->findOne();
if ($user) {
    $entityManager->removeEntity($user);
    echo "REMOVED User {$user->getId()}\n";
}

echo "PHASE3B05A_VALIDATION_CLEANUP_DONE\n";
