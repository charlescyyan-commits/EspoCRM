<?php

// Compatibility wrapper. ProspectingSummary remains provisioned by the
// canonical C17 Sales Development Command Center script.
$hasUserSelection = false;
foreach (array_slice($argv, 1) as $argument) {
    if ($argument === '--dev-defaults' || str_starts_with((string) $argument, '--user=')) {
        $hasUserSelection = true;
        break;
    }
}
if (!$hasUserSelection) {
    $argv[] = '--user=all';
}
require __DIR__ . '/phase3c17_provision_sales_development_command_center.php';
return;

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

function dashboardOptions(string $title, string $entityType, string $orderBy, ?string $primary = null): array
{
    $options = [
        'title' => $title,
        'entityType' => $entityType,
        'orderBy' => $orderBy,
        'order' => 'desc',
        'displayRecords' => 10,
        'includeShared' => true,
    ];
    if ($primary !== null) {
        $options['searchData'] = ['primary' => $primary];
    }

    return $options;
}

function provisionOperationsDashboard(
    $entityManager,
    string $userId,
    bool $includeRelatedEntityDashlets
): void
{
    $preferences = $entityManager->getEntityById('Preferences', $userId);
    if (!$preferences) {
        $preferences = $entityManager->getEntity('Preferences');
        $preferences->set('id', $userId);
        $preferences->id = $userId;
    }

    $layout = json_decode(json_encode($preferences->get('dashboardLayout')), true);
    if (!is_array($layout)) {
        $layout = [];
    }

    $tabIndex = null;
    foreach ($layout as $index => $tab) {
        if (($tab['name'] ?? null) === 'Prospecting Operations') {
            $tabIndex = $index;
            break;
        }
    }
    if ($tabIndex === null) {
        $layout[] = ['name' => 'Prospecting Operations', 'layout' => []];
        $tabIndex = array_key_last($layout);
    }

    // Phase3U03: sales-facing Prospecting Overview first; Lead ops dashlets remain below.
    $items = [
        ['id' => 'phase3u03-summary', 'name' => 'ProspectingSummary', 'x' => 0, 'y' => 0, 'width' => 4, 'height' => 2],
        ['id' => 'phase3u03-recent-discovery', 'name' => 'ProspectingRecentDiscovery', 'x' => 0, 'y' => 2, 'width' => 4, 'height' => 3],
        ['id' => 'phase3b07-tier-a', 'name' => 'ProspectingIntelligence', 'x' => 0, 'y' => 5, 'width' => 1, 'height' => 2],
        ['id' => 'phase3b07-research-pending', 'name' => 'ProspectingIntelligence', 'x' => 1, 'y' => 5, 'width' => 1, 'height' => 2],
        ['id' => 'phase3b07-contact-ready', 'name' => 'ProspectingIntelligence', 'x' => 2, 'y' => 5, 'width' => 1, 'height' => 2],
        ['id' => 'phase3b07-sync-issues', 'name' => 'ProspectingIntelligence', 'x' => 3, 'y' => 5, 'width' => 1, 'height' => 2],
        ['id' => 'phase3b07-lead-queue', 'name' => 'ProspectingIntelligence', 'x' => 0, 'y' => 7, 'width' => 4, 'height' => 3],
        ['id' => 'phase3b07-proposal-review', 'name' => 'ProspectingIntelligence', 'x' => 0, 'y' => 10, 'width' => 2, 'height' => 2],
        ['id' => 'phase3b07-missing-evidence', 'name' => 'ProspectingIntelligence', 'x' => 2, 'y' => 10, 'width' => 2, 'height' => 2],
    ];
    if ($includeRelatedEntityDashlets) {
        $items[] = ['id' => 'phase3b07-recent-evidence', 'name' => 'RecentResearchEvidence', 'x' => 0, 'y' => 12, 'width' => 2, 'height' => 2];
        $items[] = ['id' => 'phase3b07-recent-feedback', 'name' => 'RecentSalesFeedback', 'x' => 2, 'y' => 12, 'width' => 2, 'height' => 2];
    }
    $existingItems = array_filter(
        $layout[$tabIndex]['layout'] ?? [],
        fn(array $item): bool => !preg_match('/^(phase3b07|phase3u03)-/', (string) ($item['id'] ?? ''))
    );
    $layout[$tabIndex]['layout'] = array_merge(array_values($existingItems), $items);

    $options = json_decode(json_encode($preferences->get('dashletsOptions') ?: new stdClass()), true);
    if (!is_array($options)) {
        $options = [];
    }
    foreach (array_keys($options) as $id) {
        if (
            str_starts_with((string) $id, 'phase3b07-')
            || str_starts_with((string) $id, 'phase3u03-')
        ) {
            unset($options[$id]);
        }
    }
    $options['phase3u03-summary'] = ['title' => 'Prospecting Summary'];
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
    $options['phase3b07-tier-a'] = dashboardOptions('A Tier Leads', 'Lead', 'peOpportunityScoreV4', 'peTierA');
    $options['phase3b07-research-pending'] = dashboardOptions('Research Pending', 'Lead', 'peLastResearchedAt', 'peResearchPending');
    $options['phase3b07-contact-ready'] = dashboardOptions('Contact Ready', 'Lead', 'nextFollowUpAt', 'peContactReady');
    $options['phase3b07-sync-issues'] = dashboardOptions('Sync Issues', 'Lead', 'modifiedAt', 'peSyncFailed');
    $options['phase3b07-lead-queue'] = dashboardOptions('Prospecting Lead Queue', 'Lead', 'peOpportunityScoreV4');
    $options['phase3b07-proposal-review'] = dashboardOptions('Proposal Review Queue', 'Lead', 'peOpportunityScoreV4', 'peProposalReviewRequired');
    $options['phase3b07-missing-evidence'] = dashboardOptions('Completed Without Evidence', 'Lead', 'peLastResearchedAt', 'peMissingEvidence');
    if ($includeRelatedEntityDashlets) {
        $options['phase3b07-recent-evidence'] = dashboardOptions('Recent Research Evidence', 'ResearchEvidence', 'peCapturedAt');
        $options['phase3b07-recent-feedback'] = dashboardOptions('Recent Sales Feedback', 'SalesFeedback', 'createdAt', 'recentFeedback');
    }

    $preferences->set('dashboardLayout', $layout);
    $preferences->set('dashletsOptions', $options);
    $entityManager->saveEntity($preferences);
}

foreach (['admin', 'manager_test', 'sales_test'] as $userName) {
    $user = $entityManager->getRDBRepository('User')->where(['userName' => $userName])->findOne();
    if (!$user) {
        throw new \RuntimeException("Required local user is missing: {$userName}.");
    }
    provisionOperationsDashboard(
        $entityManager,
        $user->getId(),
        $userName !== 'manager_test'
    );
    echo "PHASE3B07_DASHBOARD_READY {$userName}\n";
}
