<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$leads = $entityManager->getRDBRepository('Lead')
    ->where(['name*' => 'PHASE3B03-TEST%'])
    ->find();

foreach ($leads as $lead) {
    foreach (['ResearchEvidence', 'Task'] as $entityType) {
        $foreignKey = $entityType === 'Task' ? 'parentId' : 'leadId';
        $records = $entityManager->getRDBRepository($entityType)
            ->where([$foreignKey => $lead->getId()])
            ->find();
        foreach ($records as $record) {
            $entityManager->removeEntity($record);
            echo "REMOVED {$entityType} {$record->getId()}\n";
        }
    }

    $entityManager->removeEntity($lead);
    echo "REMOVED Lead {$lead->getId()}\n";
}

$user = $entityManager->getRDBRepository('User')
    ->where(['userName' => 'phase3b03_connector_test'])
    ->findOne();
if ($user) {
    $entityManager->removeEntity($user);
    echo "REMOVED User {$user->getId()}\n";
}

echo "PHASE3B03_VALIDATION_CLEANUP_DONE\n";
