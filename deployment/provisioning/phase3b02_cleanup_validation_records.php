<?php
/**
 * Phase3B02 — Cleanup Validation Records
 *
 * Removes test Leads, Tasks, ResearchEvidence, and Opportunities
 * created during Phase3B02 pipeline validation.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$container = $app->getContainer();
$entityManager = $container->get('entityManager');

function deleteAll($entityManager, string $entityType): int
{
    $repo = $entityManager->getRDBRepository($entityType);
    $collection = $repo->where(['name*' => 'PHASE3B02-TEST-%'])->find();
    $count = 0;
    foreach ($collection as $entity) {
        $entityManager->removeEntity($entity);
        $count++;
    }
    return $count;
}

$leadCount = deleteAll($entityManager, 'Lead');
$taskCount = deleteAll($entityManager, 'Task');
$evidenceCount = deleteAll($entityManager, 'ResearchEvidence');
$oppCount = deleteAll($entityManager, 'Opportunity');

echo "CLEANUP Leads: {$leadCount}\n";
echo "CLEANUP Tasks: {$taskCount}\n";
echo "CLEANUP Evidence: {$evidenceCount}\n";
echo "CLEANUP Opportunities: {$oppCount}\n";
echo "PHASE3B02_CLEANUP_DONE\n";
