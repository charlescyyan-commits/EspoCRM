<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$leads = $entityManager->getRDBRepository('Lead')
    ->where(['name*' => '[CHITU_PHASE3B07_TEST]%'])
    ->find();

foreach ($leads as $lead) {
    $leadId = $lead->getId();
    foreach ($entityManager->getRDBRepository('LearningSignal')->where(['leadId' => $leadId])->find() as $signal) {
        $entityManager->removeEntity($signal);
        echo "REMOVED LearningSignal {$signal->getId()}\n";
    }
    foreach (['SalesFeedback', 'EmailEvent', 'ResearchEvidence'] as $entityType) {
        foreach ($entityManager->getRDBRepository($entityType)->where(['leadId' => $leadId])->find() as $record) {
            $entityManager->removeEntity($record);
            echo "REMOVED {$entityType} {$record->getId()}\n";
        }
    }
    foreach (['Task', 'Note'] as $entityType) {
        foreach ($entityManager->getRDBRepository($entityType)->where(['parentType' => 'Lead', 'parentId' => $leadId])->find() as $record) {
            $entityManager->removeEntity($record);
            echo "REMOVED {$entityType} {$record->getId()}\n";
        }
    }
    $entityManager->removeEntity($lead);
    echo "REMOVED Lead {$leadId}\n";
}

$user = $entityManager->getRDBRepository('User')->where(['userName' => 'phase3b07_validation_bot'])->findOne();
if ($user) {
    $entityManager->removeEntity($user);
    echo "REMOVED User {$user->getId()}\n";
}

echo "PHASE3B07_VALIDATION_CLEANUP_DONE\n";
