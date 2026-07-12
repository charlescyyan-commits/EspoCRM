<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$records = [
    ['ResearchEvidence', '[CHITU_PHASE3B01_VALIDATION] Evidence'],
    ['Opportunity', '[CHITU_PHASE3B01_VALIDATION] Opportunity'],
    ['Lead', '[CHITU_PHASE3B01_VALIDATION] Lead'],
    ['ResearchEvidence', '[CHITU_PHASE3B01_UI] Evidence'],
    ['Lead', '[CHITU_PHASE3B01_UI] Lead'],
];

foreach ($records as [$entityType, $name]) {
    $record = $entityManager->getRDBRepository($entityType)->where(['name' => $name])->findOne();
    if ($record) {
        $entityManager->removeEntity($record);
        echo "REMOVED {$entityType} {$record->getId()}\n";
    }
}

echo "PHASE3B01_VALIDATION_CLEANUP_DONE\n";
