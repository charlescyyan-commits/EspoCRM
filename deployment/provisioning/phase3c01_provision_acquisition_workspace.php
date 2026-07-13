<?php

require '/var/www/html/bootstrap.php';

$userName = $argv[1] ?? 'admin';
$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');
$user = $entityManager->getRDBRepository('User')->where(['userName' => $userName])->findOne();

if (!$user) {
    throw new \RuntimeException("User not found: {$userName}.");
}

$preferences = $entityManager->getEntityById('Preferences', $user->getId());
if (!$preferences) {
    $preferences = $entityManager->getEntity('Preferences');
    $preferences->set('id', $user->getId());
    $preferences->id = $user->getId();
}

$layout = json_decode(json_encode($preferences->get('dashboardLayout')), true);
if (!is_array($layout)) {
    $layout = [];
}

$tabIndex = null;
foreach ($layout as $index => $tab) {
    if (($tab['name'] ?? null) === 'Acquisition') {
        $tabIndex = $index;
        break;
    }
}
if ($tabIndex === null) {
    $layout[] = ['name' => 'Acquisition', 'layout' => []];
    $tabIndex = array_key_last($layout);
}

$items = [
    ['id' => 'phase3c01-discovery-jobs', 'name' => 'AcquisitionDiscoveryJobs', 'x' => 0, 'y' => 0, 'width' => 2, 'height' => 2],
    ['id' => 'phase3c01-running', 'name' => 'AcquisitionJobsRunning', 'x' => 2, 'y' => 0, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-waiting', 'name' => 'AcquisitionJobsWaiting', 'x' => 3, 'y' => 0, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-completed', 'name' => 'AcquisitionJobsCompleted', 'x' => 0, 'y' => 2, 'width' => 2, 'height' => 2],
    ['id' => 'phase3c01-failed', 'name' => 'AcquisitionJobsFailed', 'x' => 2, 'y' => 2, 'width' => 2, 'height' => 2],
    ['id' => 'phase3c01-lead-pool', 'name' => 'AcquisitionLeadPool', 'x' => 0, 'y' => 4, 'width' => 2, 'height' => 3],
    ['id' => 'phase3c01-research-queue', 'name' => 'AcquisitionResearchQueue', 'x' => 2, 'y' => 4, 'width' => 2, 'height' => 3],
];

$layout[$tabIndex]['layout'] = array_merge(
    array_values(array_filter(
        $layout[$tabIndex]['layout'] ?? [],
        fn(array $item): bool => !str_starts_with((string) ($item['id'] ?? ''), 'phase3c01-')
    )),
    $items
);

$options = json_decode(json_encode($preferences->get('dashletsOptions') ?: new stdClass()), true);
if (!is_array($options)) {
    $options = [];
}
foreach (array_keys($options) as $id) {
    if (str_starts_with((string) $id, 'phase3c01-')) {
        unset($options[$id]);
    }
}

function phase3c01Dashlet(string $title, string $entityType, string $orderBy, ?string $primary = null): array
{
    $options = ['title' => $title, 'entityType' => $entityType, 'orderBy' => $orderBy, 'order' => 'desc', 'displayRecords' => 10, 'includeShared' => true];
    if ($primary !== null) {
        $options['searchData'] = ['primary' => $primary];
    }
    return $options;
}

$options['phase3c01-discovery-jobs'] = phase3c01Dashlet('Discovery Jobs', 'SearchJob', 'createdAt');
$options['phase3c01-running'] = phase3c01Dashlet('Running', 'SearchJob', 'createdAt', 'jobsRunning');
$options['phase3c01-waiting'] = phase3c01Dashlet('Waiting', 'SearchJob', 'createdAt', 'jobsWaiting');
$options['phase3c01-completed'] = phase3c01Dashlet('Completed', 'SearchJob', 'completedAt', 'jobsCompleted');
$options['phase3c01-failed'] = phase3c01Dashlet('Failed', 'SearchJob', 'createdAt', 'jobsFailed');
$options['phase3c01-lead-pool'] = phase3c01Dashlet('Lead Pool', 'ProspectPool', 'createdAt');
$options['phase3c01-research-queue'] = phase3c01Dashlet('Research Queue', 'ProspectPool', 'createdAt', 'researchQueue');

$preferences->set('dashboardLayout', $layout);
$preferences->set('dashletsOptions', $options);
$entityManager->saveEntity($preferences);

echo "PHASE3C01_ACQUISITION_WORKSPACE_READY {$userName}\n";
