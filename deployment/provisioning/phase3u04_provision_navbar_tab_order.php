<?php

declare(strict_types=1);

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();

$container = $app->getContainer();
$config = $container->get('config');
$injectableFactory = $container->getByClass(\Espo\Core\InjectableFactory::class);
$configWriter = $injectableFactory->create(\Espo\Core\Utils\Config\ConfigWriter::class);

$hiddenNavigationItems = [
    'Meeting',
    'Call',
    'Case',
    'Ticket',
    'ProspectingDashboard',
    'ProspectingSearch',
    'SearchStrategy',
    'SearchJob',
    'ProspectPool',
    'ResearchEvidence',
];

$prospectingNavigationGroup = [
    [
        'type' => 'divider',
        'text' => 'Prospecting',
        'id' => 'phase3u04-prospecting',
    ],
    'ProspectingSearch',
    'SearchJob',
    'ProspectPool',
    'ResearchEvidence',
];

$tabList = $config->get('tabList', []);
if (!is_array($tabList)) {
    throw new \RuntimeException('Expected tabList to be an array.');
}

// Preserve all remaining CRM tabs and dividers. Remove only the requested hidden
// modules, prior Prospecting entries, and the previous Prospecting divider so the
// native tab-list grouping is deterministic and safe to run repeatedly.
$tabList = array_values(array_filter(
    $tabList,
    static function ($item) use ($hiddenNavigationItems): bool {
        if (is_string($item)) {
            return !in_array($item, $hiddenNavigationItems, true);
        }

        $dividerId = is_array($item)
            ? ($item['id'] ?? null)
            : (is_object($item) ? ($item->id ?? null) : null);

        if ($dividerId === 'phase3u04-prospecting') {
            return false;
        }

        return true;
    }
));

$configWriter->set('tabList', array_merge($tabList, $prospectingNavigationGroup));
$configWriter->save();

echo 'PHASE3U04_NAVIGATION_READY Prospecting:Search,SearchJob,ProspectPool,ResearchEvidence' . PHP_EOL;
