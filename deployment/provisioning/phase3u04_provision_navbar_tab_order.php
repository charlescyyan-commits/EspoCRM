<?php

declare(strict_types=1);

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();

$container = $app->getContainer();
$config = $container->get('config');
$injectableFactory = $container->getByClass(\Espo\Core\InjectableFactory::class);
$configWriter = $injectableFactory->create(\Espo\Core\Utils\Config\ConfigWriter::class);

$prospectingTabs = [
    'ProspectingDashboard',
    'ProspectingSearch',
    'SearchStrategy',
    'SearchJob',
    'ProspectPool',
    'ResearchEvidence',
];

$tabList = $config->get('tabList', []);
if (!is_array($tabList)) {
    throw new \RuntimeException('Expected tabList to be an array.');
}

// Preserve every existing CRM tab and divider exactly as configured. Remove only
// previous copies of the Prospecting entries so the requested workflow order is
// deterministic and the script is safe to run repeatedly.
$tabList = array_values(array_filter(
    $tabList,
    static fn ($item): bool => !is_string($item) || !in_array($item, $prospectingTabs, true)
));

$configWriter->set('tabList', array_merge($tabList, $prospectingTabs));
$configWriter->save();

echo 'PHASE3U04_TAB_LIST_READY ' . implode(',', $prospectingTabs) . PHP_EOL;
