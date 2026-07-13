<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$leads = $entityManager->getRDBRepository('Lead')
    ->where(['peCandidateId' => 'phase3b06_1-test-candidate'])
    ->find();

foreach ($leads as $lead) {
    $leadId = $lead->getId();
    foreach (['ResearchEvidence', 'Task'] as $entityType) {
        $foreignKey = $entityType === 'Task' ? 'parentId' : 'leadId';
        foreach ($entityManager->getRDBRepository($entityType)->where([$foreignKey => $leadId])->find() as $record) {
            $entityManager->removeEntity($record);
            echo "REMOVED {$entityType} {$record->getId()}\n";
        }
    }
    $entityManager->removeEntity($lead);
    echo "REMOVED Lead {$leadId}\n";
}

$user = $entityManager->getRDBRepository('User')
    ->where(['userName' => 'phase3b06_1_connector_test'])
    ->findOne();
if ($user) {
    $entityManager->removeEntity($user);
    echo "REMOVED User {$user->getId()}\n";
}

echo "PHASE3B06_1_VALIDATION_CLEANUP_DONE\n";
