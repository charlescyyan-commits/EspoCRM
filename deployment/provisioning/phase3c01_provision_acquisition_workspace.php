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
    $tabName = $tab['name'] ?? null;
    if ($tabName === 'Prospecting Home' || $tabName === 'Acquisition') {
        $tabIndex = $index;
        break;
    }
}
if ($tabIndex === null) {
    $layout[] = ['name' => 'Prospecting Home', 'layout' => []];
    $tabIndex = array_key_last($layout);
}

$layout[$tabIndex]['name'] = 'Prospecting Home';

$items = [
    ['id' => 'phase3u03-summary', 'name' => 'ProspectingSummary', 'x' => 0, 'y' => 0, 'width' => 4, 'height' => 2],
    ['id' => 'phase3u03-recent-discovery', 'name' => 'ProspectingRecentDiscovery', 'x' => 0, 'y' => 2, 'width' => 4, 'height' => 3],
    ['id' => 'phase3c02-search-strategies', 'name' => 'AcquisitionSearchStrategies', 'x' => 0, 'y' => 5, 'width' => 2, 'height' => 2],
    ['id' => 'phase3c01-discovery-jobs', 'name' => 'AcquisitionDiscoveryJobs', 'x' => 2, 'y' => 5, 'width' => 2, 'height' => 2],
    ['id' => 'phase3c01-running', 'name' => 'AcquisitionJobsRunning', 'x' => 0, 'y' => 7, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-waiting', 'name' => 'AcquisitionJobsWaiting', 'x' => 1, 'y' => 7, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-completed', 'name' => 'AcquisitionJobsCompleted', 'x' => 2, 'y' => 7, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-failed', 'name' => 'AcquisitionJobsFailed', 'x' => 3, 'y' => 7, 'width' => 1, 'height' => 2],
    ['id' => 'phase3c01-lead-pool', 'name' => 'AcquisitionLeadPool', 'x' => 0, 'y' => 9, 'width' => 2, 'height' => 3],
    ['id' => 'phase3c01-research-queue', 'name' => 'AcquisitionResearchQueue', 'x' => 2, 'y' => 9, 'width' => 2, 'height' => 3],
];

$layout[$tabIndex]['layout'] = array_merge(
    array_values(array_filter(
        $layout[$tabIndex]['layout'] ?? [],
        fn(array $item): bool => !preg_match('/^(phase3c0[12]|phase3u03)-/', (string) ($item['id'] ?? ''))
    )),
    $items
);

$options = json_decode(json_encode($preferences->get('dashletsOptions') ?: new stdClass()), true);
if (!is_array($options)) {
    $options = [];
}
foreach (array_keys($options) as $id) {
    if (preg_match('/^(phase3c0[12]|phase3u03)-/', (string) $id)) {
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

$options['phase3u03-summary'] = [
    'title' => 'Prospecting Summary',
];
$options['phase3u03-recent-discovery'] = [
    'title' => 'Recent Discovery Activity',
    'entityType' => 'SearchJob',
    'orderBy' => 'createdAt',
    'order' => 'desc',
    'displayRecords' => 8,
    'includeShared' => true,
    'expandedLayout' => [
        'rows' => [
            [['name' => 'name', 'link' => true], ['name' => 'status']],
            [['name' => 'createdAt'], ['name' => 'resultCount']],
        ],
    ],
];
$options['phase3c02-search-strategies'] = phase3c01Dashlet('Search Strategies', 'SearchStrategy', 'createdAt');
$options['phase3c01-discovery-jobs'] = phase3c01Dashlet('Discovery Jobs', 'SearchJob', 'createdAt');
$options['phase3c01-running'] = phase3c01Dashlet('Running Jobs', 'SearchJob', 'createdAt', 'jobsRunning');
$options['phase3c01-waiting'] = phase3c01Dashlet('Queued Jobs', 'SearchJob', 'createdAt', 'jobsQueued');
$options['phase3c01-completed'] = phase3c01Dashlet('Completed Jobs', 'SearchJob', 'completedAt', 'jobsCompleted');
$options['phase3c01-failed'] = phase3c01Dashlet('Failed Jobs', 'SearchJob', 'createdAt', 'jobsFailed');
$options['phase3c01-lead-pool'] = phase3c01Dashlet('Lead Pool', 'ProspectPool', 'createdAt');
$options['phase3c01-research-queue'] = phase3c01Dashlet('Research Queue', 'ProspectPool', 'createdAt', 'researchQueue');

$preferences->set('dashboardLayout', $layout);
$preferences->set('dashletsOptions', $options);
$entityManager->saveEntity($preferences);

echo "PHASE3C01_ACQUISITION_WORKSPACE_READY {$userName}\n";
