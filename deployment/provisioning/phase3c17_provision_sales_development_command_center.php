<?php

declare(strict_types=1);

/**
 * Canonical Phase3C17 Sales Development Command Center provisioner.
 *
 * Usage:
 *   php phase3c17_provision_sales_development_command_center.php
 *   php phase3c17_provision_sales_development_command_center.php --user=admin
 *
 * This presentation-only script merges phase-managed dashboard tabs into one
 * primary Chinese-first dashboard. It preserves My Espo and non-phase dashlets.
 */

const PHASE3C17_COMMAND_CENTER = '销售开发指挥中心';

/** @return array<int, string> */
function phase3c17TargetUsers(array $arguments): array
{
    foreach (array_slice($arguments, 1) as $argument) {
        if (str_starts_with($argument, '--user=')) {
            $userName = substr($argument, strlen('--user='));
            if ($userName === '' || $userName === 'all') {
                break;
            }

            return [$userName];
        }

        throw new \InvalidArgumentException('Unknown argument: ' . $argument);
    }

    return ['admin', 'manager_test', 'sales_test'];
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

function phase3c17ProvisionCommandCenter($entityManager, string $userName): void
{
    $user = $entityManager->getRDBRepository('User')->where(['userName' => $userName])->findOne();
    if (!$user) {
        throw new \RuntimeException("Required local user is missing: {$userName}.");
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

    $legacyTabs = ['Prospecting Operations', 'Acquisition', 'Prospecting Home', PHASE3C17_COMMAND_CENTER];
    $preservedTabs = [];
    $carriedItems = [];
    foreach ($layout as $tab) {
        if (!is_array($tab)) {
            continue;
        }
        if (!in_array($tab['name'] ?? null, $legacyTabs, true)) {
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

    $preservedTabs[] = [
        'name' => PHASE3C17_COMMAND_CENTER,
        'layout' => array_merge(phase3c17CommandCenterItems(), $carriedItems),
    ];

    $options = json_decode(json_encode($preferences->get('dashletsOptions') ?: new \stdClass()), true);
    if (!is_array($options)) {
        $options = [];
    }
    foreach (array_keys($options) as $id) {
        if (phase3c17IsManagedDashletId((string) $id)) {
            unset($options[$id]);
        }
    }

    $options['phase3c17-command-summary'] = ['title' => '潜客运营'];
    $options['phase3c17-command-overview'] = ['title' => '搜索中心'];
    $options['phase3c17-command-my-tasks'] = phase3c17RecordsOptions('我的任务', 'Task', 'actual', 'dateStart', 'asc', ['onlyMy']);
    $options['phase3c17-command-research'] = ['title' => '待研究客户'];
    $options['phase3c17-command-outreach'] = phase3c17RecordsOptions('待触达', 'DraftApproval', 'c17Pending', 'createdAt');
    $options['phase3c17-command-replies'] = phase3c17RecordsOptions('待回复', 'ReplyEvent', 'c17AwaitingReply', 'receivedAt');
    $options['phase3c17-command-approvals'] = phase3c17RecordsOptions('待审批', 'Approval', 'c17Pending', 'createdAt');
    $options['phase3c17-command-pool'] = ['title' => '客户池'];
    $options['phase3c17-command-recent-discovery'] = ['title' => '新增客户'];
    $options['phase3c17-command-completed'] = ['title' => '研究完成（任务）'];
    $options['phase3c17-command-evidence'] = ['title' => '研究完成（证据）'];

    $preferences->set('dashboardLayout', $preservedTabs);
    $preferences->set('dashletsOptions', $options);
    $entityManager->saveEntity($preferences);
    echo "PHASE3C17_COMMAND_CENTER_READY {$userName}\n";
}

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

foreach (phase3c17TargetUsers($argv) as $userName) {
    phase3c17ProvisionCommandCenter($entityManager, $userName);
}
