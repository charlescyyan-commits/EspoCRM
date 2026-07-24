<?php

declare(strict_types=1);

/**
 * Canonical Phase3C17 Sales Development Command Center provisioner.
 *
 * Usage:
 *   php phase3c17_provision_sales_development_command_center.php --user=admin
 *   php phase3c17_provision_sales_development_command_center.php --user=all
 *   php phase3c17_provision_sales_development_command_center.php --dev-defaults
 *
 * Presentation-only: merges phase-managed dashboard tabs into one primary
 * Chinese-first dashboard tab. Preserves My Espo and non-phase dashlets.
 *
 * CC-1 center responsibility boundary (composition only — no lifecycle logic
 * is duplicated here; queues are read-only Records/record-list dashlets):
 *   潜客运营 (this Command Center tab): team operational overview answering
 *     "我今天应该做什么？" — summary cards, daily queues, operational counters.
 *   搜索中心: search strategy/jobs ownership (SearchStrategy, SearchJob, ProspectPool).
 *   触达中心: outreach + reply visibility (DraftApproval, SendExecution, ReplyEvent).
 *   报价中心: quote + approval visibility (Quote, Approval, ProformaInvoice).
 *
 * New-user strategy (no login-time hook):
 *   A. Native EspoCRM system default dashboard / Dashboard Templates apply to
 *      newly created users (Administration > User Interface / Dashboard Templates).
 *   B. Re-run this script with --user=all after creating users.
 *   C. Extension metadata does not override app/defaultDashboardLayouts here so
 *      Standard "My Espo" composition stays under admin/product control.
 */

const PHASE3C17_COMMAND_CENTER = '销售开发指挥中心';

/** @var array<int, string> */
const PHASE3C17_DEV_DEFAULT_USERS = ['admin', 'manager_test', 'sales_test'];

/** @var array<int, string> */
const PHASE3C17_LEGACY_TABS = [
    'Prospecting Operations',
    'Acquisition',
    'Prospecting Home',
    PHASE3C17_COMMAND_CENTER,
];

/**
 * Parse CLI user-selection flags. Does not resolve --user=all against the DB.
 *
 * @return array{mode: string, names: array<int, string>}
 */
function phase3c17ParseUserSelection(array $arguments): array
{
    $mode = null;
    $names = [];

    foreach (array_slice($arguments, 1) as $argument) {
        if ($argument === '--dev-defaults') {
            if ($mode !== null) {
                throw new \InvalidArgumentException(
                    'Conflicting user selection flags. Use only one of --user=<name>, --user=all, or --dev-defaults.'
                );
            }
            $mode = 'dev-defaults';
            $names = PHASE3C17_DEV_DEFAULT_USERS;
            continue;
        }

        if (str_starts_with($argument, '--user=')) {
            if ($mode !== null) {
                throw new \InvalidArgumentException(
                    'Conflicting user selection flags. Use only one of --user=<name>, --user=all, or --dev-defaults.'
                );
            }

            $userName = substr($argument, strlen('--user='));
            if ($userName === '') {
                throw new \InvalidArgumentException(
                    'Empty --user= value. Use --user=<userName> or --user=all.'
                );
            }
            if ($userName === 'all') {
                $mode = 'all';
                $names = [];
                continue;
            }

            $mode = 'named';
            $names = [$userName];
            continue;
        }

        throw new \InvalidArgumentException('Unknown argument: ' . $argument);
    }

    if ($mode === null) {
        throw new \InvalidArgumentException(
            'User selection required. Pass --user=<userName>, --user=all, or --dev-defaults (local development only).'
        );
    }

    return ['mode' => $mode, 'names' => $names];
}

/**
 * Active internal users eligible for Command Center Preferences writes.
 * Excludes portal, api, and system users. Soft-deleted rows are excluded by ORM.
 *
 * @return array<int, string>
 */
function phase3c17ResolveEligibleUserNames($entityManager): array
{
    $users = $entityManager
        ->getRDBRepository('User')
        ->where([
            'isActive' => true,
            'type!=' => ['portal', 'api', 'system'],
            'userName!=' => 'system',
        ])
        ->order('userName')
        ->find();

    $names = [];
    foreach ($users as $user) {
        $userName = (string) $user->get('userName');
        if ($userName === '') {
            continue;
        }
        $names[] = $userName;
    }

    return $names;
}

/**
 * @return array<int, string>
 */
function phase3c17ResolveTargetUsers(array $arguments, $entityManager): array
{
    $selection = phase3c17ParseUserSelection($arguments);

    if ($selection['mode'] === 'all') {
        $names = phase3c17ResolveEligibleUserNames($entityManager);
    } elseif ($selection['mode'] === 'dev-defaults') {
        echo "DEV-DEFAULTS: targeting local test usernames only.\n";
        $names = $selection['names'];
    } else {
        $names = $selection['names'];
    }

    echo "Users selected:\n";
    echo count($names) . "\n";

    return $names;
}

function phase3c17IsManagedDashletId(string $id): bool
{
    return preg_match('/^(phase3(?:u03|b07|c0[12]|c17)-)/', $id) === 1;
}

function phase3c17RecordsOptions(
    string $title,
    string $entityType,
    string $primaryFilter,
    string $sortBy,
    string $sortDirection = 'desc',
    array $boolFilterList = []
): array {
    return [
        'title' => $title,
        'entityType' => $entityType,
        'primaryFilter' => $primaryFilter,
        'boolFilterList' => $boolFilterList,
        'sortBy' => $sortBy,
        'sortDirection' => $sortDirection,
        'displayRecords' => 10,
        'expandedLayout' => ['rows' => []],
    ];
}

/** @return array<int, array<string, int|string>> */
function phase3c17CommandCenterItems(): array
{
    return [
        // TOP: operational summaries; both dashlets already exist in the extension.
        ['id' => 'phase3c17-command-summary', 'name' => 'ProspectingSummary', 'x' => 0, 'y' => 0, 'width' => 2, 'height' => 2],
        ['id' => 'phase3c17-command-overview', 'name' => 'AcquisitionOverview', 'x' => 2, 'y' => 0, 'width' => 2, 'height' => 2],
        // MIDDLE: daily queues. Records is an EspoCRM native dashlet.
        ['id' => 'phase3c17-command-my-tasks', 'name' => 'Records', 'x' => 0, 'y' => 2, 'width' => 2, 'height' => 3],
        ['id' => 'phase3c17-command-research', 'name' => 'AcquisitionResearchQueue', 'x' => 2, 'y' => 2, 'width' => 2, 'height' => 3],
        ['id' => 'phase3c17-command-outreach', 'name' => 'Records', 'x' => 0, 'y' => 5, 'width' => 1, 'height' => 3],
        ['id' => 'phase3c17-command-replies', 'name' => 'Records', 'x' => 1, 'y' => 5, 'width' => 1, 'height' => 3],
        ['id' => 'phase3c17-command-approvals', 'name' => 'Records', 'x' => 2, 'y' => 5, 'width' => 2, 'height' => 3],
        // BOTTOM: existing acquisition and evidence metrics/activity dashlets.
        ['id' => 'phase3c17-command-pool', 'name' => 'AcquisitionLeadPool', 'x' => 0, 'y' => 8, 'width' => 2, 'height' => 3],
        ['id' => 'phase3c17-command-recent-discovery', 'name' => 'ProspectingRecentDiscovery', 'x' => 2, 'y' => 8, 'width' => 2, 'height' => 3],
        ['id' => 'phase3c17-command-completed', 'name' => 'AcquisitionJobsCompleted', 'x' => 0, 'y' => 11, 'width' => 2, 'height' => 3],
        ['id' => 'phase3c17-command-evidence', 'name' => 'RecentResearchEvidence', 'x' => 2, 'y' => 11, 'width' => 2, 'height' => 3],
    ];
}

/**
 * Build the Preferences dashboardLayout with Command Center as the first tab.
 * Removes managed legacy Phase3C17 tabs; preserves personal dashboards (e.g. My Espo).
 *
 * @param array<int, mixed> $layout
 * @return array{0: array<int, array<string, mixed>>, 1: array<int, array<string, mixed>>}
 */
function phase3c17BuildDashboardLayout(array $layout): array
{
    $preservedTabs = [];
    $carriedItems = [];

    foreach ($layout as $tab) {
        if (!is_array($tab)) {
            continue;
        }
        if (!in_array($tab['name'] ?? null, PHASE3C17_LEGACY_TABS, true)) {
            $preservedTabs[] = $tab;
            continue;
        }

        foreach ($tab['layout'] ?? [] as $item) {
            if (!is_array($item) || phase3c17IsManagedDashletId((string) ($item['id'] ?? ''))) {
                continue;
            }
            $item['y'] = max(14, (int) ($item['y'] ?? 0) + 14);
            $carriedItems[] = $item;
        }
    }

    $commandCenterTab = [
        'name' => PHASE3C17_COMMAND_CENTER,
        'layout' => array_merge(phase3c17CommandCenterItems(), $carriedItems),
    ];

    // Command Center is always the first dashboard tab.
    return [array_merge([$commandCenterTab], $preservedTabs), $carriedItems];
}

/** @return array<string, mixed> */
function phase3c17BuildDashletsOptions(array $options): array
{
    foreach (array_keys($options) as $id) {
        if (phase3c17IsManagedDashletId((string) $id)) {
            unset($options[$id]);
        }
    }

    $options['phase3c17-command-summary'] = ['title' => '潜客概览'];
    $options['phase3c17-command-overview'] = ['title' => '获客概览'];
    $options['phase3c17-command-my-tasks'] = phase3c17RecordsOptions('我的任务', 'Task', 'actual', 'dateStart', 'asc', ['onlyMy']);
    $options['phase3c17-command-research'] = ['title' => '待研究客户'];
    $options['phase3c17-command-outreach'] = phase3c17RecordsOptions('待触达', 'DraftApproval', 'c17Pending', 'createdAt');
    $options['phase3c17-command-replies'] = phase3c17RecordsOptions('待回复', 'ReplyEvent', 'c17AwaitingReply', 'receivedAt');
    $options['phase3c17-command-approvals'] = phase3c17RecordsOptions('待审批', 'Approval', 'c17Pending', 'createdAt');
    $options['phase3c17-command-pool'] = ['title' => '客户池'];
    $options['phase3c17-command-recent-discovery'] = ['title' => '新增客户'];
    $options['phase3c17-command-completed'] = ['title' => '研究完成（任务）'];
    $options['phase3c17-command-evidence'] = ['title' => '研究完成（证据）'];

    return $options;
}

/**
 * Provision one user. Returns processed|skipped|failed for batch summaries.
 */
function phase3c17ProvisionCommandCenter($entityManager, string $userName): string
{
    $user = $entityManager->getRDBRepository('User')->where(['userName' => $userName])->findOne();
    if (!$user) {
        echo "WARNING: user not found, skipping: {$userName}\n";
        return 'skipped';
    }

    try {
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

        [$dashboardLayout] = phase3c17BuildDashboardLayout($layout);

        $options = json_decode(json_encode($preferences->get('dashletsOptions') ?: new \stdClass()), true);
        if (!is_array($options)) {
            $options = [];
        }
        $options = phase3c17BuildDashletsOptions($options);

        $preferences->set('dashboardLayout', $dashboardLayout);
        $preferences->set('dashletsOptions', $options);
        $entityManager->saveEntity($preferences);
        echo "PHASE3C17_COMMAND_CENTER_READY {$userName}\n";

        return 'processed';
    } catch (\Throwable $exception) {
        echo "ERROR: failed provisioning {$userName}: {$exception->getMessage()}\n";
        return 'failed';
    }
}

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$processed = 0;
$skipped = 0;
$failed = 0;

foreach (phase3c17ResolveTargetUsers($argv, $entityManager) as $userName) {
    $status = phase3c17ProvisionCommandCenter($entityManager, $userName);
    if ($status === 'processed') {
        $processed++;
    } elseif ($status === 'skipped') {
        $skipped++;
    } else {
        $failed++;
    }
}

echo "Processed:\n{$processed}\n";
echo "Skipped:\n{$skipped}\n";
echo "Failed:\n{$failed}\n";

if ($failed > 0) {
    exit(1);
}
