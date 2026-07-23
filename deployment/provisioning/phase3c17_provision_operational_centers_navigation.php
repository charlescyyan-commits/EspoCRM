<?php

declare(strict_types=1);

/**
 * Canonical Phase3C17 global navigation materializer.
 *
 * Usage:
 *   php phase3c17_provision_operational_centers_navigation.php \
 *     --desired=/path/phase3c17_navigation.json \
 *     --snapshot=/safe/path/pre-c17-navigation.json
 *
 * Re-running with the same snapshot path is safe: the original snapshot is
 * validated and retained rather than overwritten. Restore with:
 *   php phase3c17_provision_operational_centers_navigation.php \
 *     --restore=/safe/path/pre-c17-navigation.json
 */

const PHASE3C17_NAVIGATION_MARKER = 'phase3c17-wp1-4-product-polish-v1';
const PHASE3C17_SNAPSHOT_SCHEMA_VERSION = 1;

/**
 * @return array<string, string|bool>
 */
function phase3c17ParseArguments(array $arguments): array
{
    $options = [
        'desired' => dirname(__DIR__) . '/navigation/phase3c17_navigation.json',
        'snapshot' => '',
        'restore' => '',
        'dryRun' => false,
    ];

    foreach (array_slice($arguments, 1) as $argument) {
        if ($argument === '--dry-run') {
            $options['dryRun'] = true;
            continue;
        }

        foreach (['desired', 'snapshot', 'restore'] as $name) {
            $prefix = '--' . $name . '=';
            if (str_starts_with($argument, $prefix)) {
                $options[$name] = substr($argument, strlen($prefix));
                continue 2;
            }
        }

        throw new \InvalidArgumentException('Unknown argument: ' . $argument);
    }

    return $options;
}

/**
 * @return array<string, mixed>
 */
function phase3c17LoadJson(string $path, string $description): array
{
    if (!is_file($path)) {
        throw new \RuntimeException($description . ' file not found: ' . $path);
    }

    $decoded = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($decoded)) {
        throw new \RuntimeException($description . ' must contain a JSON object.');
    }

    return $decoded;
}

/**
 * @param array<string, mixed> $desired
 */
function phase3c17ValidateDesiredState(array $desired): void
{
    if (($desired['schemaVersion'] ?? null) !== 1) {
        throw new \RuntimeException('Unsupported navigation schemaVersion.');
    }
    if (($desired['navigationVersion'] ?? null) !== PHASE3C17_NAVIGATION_MARKER) {
        throw new \RuntimeException('Navigation version marker mismatch.');
    }

    foreach (
        [
            'prospectingEntries',
            'requiredPreservedGlobalEntries',
            'managedProspectingEntries',
            'managedTopLevelEntries',
            'legacyDividerIds',
            'legacyDividerTexts',
        ] as $field
    ) {
        $value = $desired[$field] ?? null;
        if (!is_array($value) || $value === [] || array_filter($value, 'is_string') !== $value) {
            throw new \RuntimeException('Desired state requires a non-empty string list: ' . $field);
        }
        if (count($value) !== count(array_unique($value))) {
            throw new \RuntimeException('Desired state list contains duplicates: ' . $field);
        }
    }

    foreach ($desired['prospectingEntries'] as $entry) {
        if (!in_array($entry, $desired['managedProspectingEntries'], true)) {
            throw new \RuntimeException('Prospecting entry is not governed: ' . $entry);
        }
    }

    foreach ($desired['managedProspectingEntries'] as $entry) {
        if (!in_array($entry, $desired['managedTopLevelEntries'], true)) {
            throw new \RuntimeException('Prospecting entry is not managed at the top level: ' . $entry);
        }
    }

    $topLevelOrder = $desired['topLevelOrder'] ?? null;
    if (!is_array($topLevelOrder) || $topLevelOrder === []) {
        throw new \RuntimeException('Desired state requires a non-empty topLevelOrder.');
    }

    foreach ($topLevelOrder as $item) {
        if (is_string($item)) {
            continue;
        }
        if (
            !is_array($item)
            || ($item['type'] ?? null) !== 'divider'
            || !is_string($item['text'] ?? null)
            || !is_string($item['id'] ?? null)
        ) {
            throw new \RuntimeException('topLevelOrder requires only strings or valid dividers.');
        }
    }

    if (($topLevelOrder[0] ?? null) !== 'Home') {
        throw new \RuntimeException('The native Home entry must remain first in the product IA.');
    }
}

function phase3c17DividerId(mixed $item): ?string
{
    $dividerId = is_array($item)
        ? ($item['id'] ?? null)
        : (is_object($item) ? ($item->id ?? null) : null);

    return is_string($dividerId) ? $dividerId : null;
}

function phase3c17DividerText(mixed $item): ?string
{
    $text = is_array($item)
        ? ($item['text'] ?? null)
        : (is_object($item) ? ($item->text ?? null) : null);

    return is_string($text) ? $text : null;
}

function phase3c17IsDivider(mixed $item): bool
{
    return is_array($item) && ($item['type'] ?? null) === 'divider';
}

/**
 * Remove divider-only gaps left by relocating governed native entries while
 * retaining any non-governed native administration sections in their order.
 *
 * @param array<int, mixed> $items
 * @return array<int, mixed>
 */
function phase3c17CompactPreservedNavigation(array $items): array
{
    $compacted = [];
    $pendingDivider = null;

    foreach ($items as $item) {
        if (phase3c17IsDivider($item)) {
            $pendingDivider = $item;
            continue;
        }

        if ($pendingDivider !== null) {
            $compacted[] = $pendingDivider;
            $pendingDivider = null;
        }
        $compacted[] = $item;
    }

    return $compacted;
}

/**
 * @param array<int, mixed> $tabList
 * @param array<string, mixed> $desired
 * @return array<int, mixed>
 */
function phase3c17Materialize(array $tabList, array $desired): array
{
    foreach ($desired['requiredPreservedGlobalEntries'] as $requiredEntry) {
        $matches = array_values(array_filter(
            $tabList,
            static fn (mixed $item): bool => $item === $requiredEntry
        ));
        if (count($matches) !== 1) {
            throw new \RuntimeException(
                'Expected exactly one preserved global navigation entry: ' . $requiredEntry
            );
        }
    }

    $managedEntries = $desired['managedTopLevelEntries'];
    $legacyDividerIds = $desired['legacyDividerIds'];
    $legacyDividerTexts = $desired['legacyDividerTexts'];

    $preserved = phase3c17CompactPreservedNavigation(array_values(array_filter(
        $tabList,
        static function (mixed $item) use (
            $managedEntries,
            $legacyDividerIds,
            $legacyDividerTexts
        ): bool {
            if (is_string($item)) {
                return $item !== '_delimiter_' && !in_array($item, $managedEntries, true);
            }

            if (!phase3c17IsDivider($item)) {
                return true;
            }

            $dividerId = phase3c17DividerId($item);
            $dividerText = phase3c17DividerText($item);

            return (
                ($dividerId === null || !in_array($dividerId, $legacyDividerIds, true))
                && $dividerText !== null
                && !in_array($dividerText, $legacyDividerTexts, true)
            );
        }
    )));

    $governedOrder = array_values(array_filter(
        $desired['topLevelOrder'],
        static fn (mixed $item): bool => $item !== 'Home'
    ));

    return array_merge(
        $governedOrder,
        $preserved
    );
}

/**
 * @param array<int, mixed> $tabList
 */
function phase3c17WriteSnapshot(string $path, array $tabList): void
{
    if (is_file($path)) {
        $existing = phase3c17LoadJson($path, 'Existing navigation snapshot');
        if (
            ($existing['schemaVersion'] ?? null) !== PHASE3C17_SNAPSHOT_SCHEMA_VERSION
            || !is_array($existing['tabList'] ?? null)
        ) {
            throw new \RuntimeException('Existing snapshot is invalid and will not be overwritten.');
        }
        echo 'PHASE3C17_SNAPSHOT_RETAINED ' . $path . PHP_EOL;
        return;
    }

    $payload = [
        'schemaVersion' => PHASE3C17_SNAPSHOT_SCHEMA_VERSION,
        'navigationVersion' => PHASE3C17_NAVIGATION_MARKER,
        'capturedAt' => gmdate('c'),
        'environment' => gethostname() ?: 'unknown',
        'tabListSha256' => hash('sha256', json_encode($tabList, JSON_THROW_ON_ERROR)),
        'tabList' => $tabList,
    ];
    $json = json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    if (file_put_contents($path, $json . PHP_EOL, LOCK_EX) === false) {
        throw new \RuntimeException('Unable to write navigation snapshot: ' . $path);
    }
    echo 'PHASE3C17_SNAPSHOT_CREATED ' . $path . PHP_EOL;
}

$options = phase3c17ParseArguments($argv);

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();

$container = $app->getContainer();
$config = $container->get('config');
$injectableFactory = $container->getByClass(\Espo\Core\InjectableFactory::class);
$configWriter = $injectableFactory->create(\Espo\Core\Utils\Config\ConfigWriter::class);

$tabList = $config->get('tabList', []);
if (!is_array($tabList)) {
    throw new \RuntimeException('Expected runtime config.tabList to be an array.');
}

echo 'PHASE3C17_NAVIGATION_BEFORE ' .
    json_encode($tabList, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR) .
    PHP_EOL;

if ($options['restore'] !== '') {
    $snapshot = phase3c17LoadJson((string) $options['restore'], 'Navigation snapshot');
    if (
        ($snapshot['schemaVersion'] ?? null) !== PHASE3C17_SNAPSHOT_SCHEMA_VERSION
        || !is_array($snapshot['tabList'] ?? null)
    ) {
        throw new \RuntimeException('Navigation snapshot schema is invalid.');
    }

    $restored = $snapshot['tabList'];
    if ($options['dryRun'] !== true) {
        $configWriter->set('tabList', $restored);
        $configWriter->save();
    }
    echo 'PHASE3C17_NAVIGATION_RESTORED ' .
        json_encode($restored, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR) .
        PHP_EOL;
    exit(0);
}

$desired = phase3c17LoadJson((string) $options['desired'], 'Desired navigation state');
phase3c17ValidateDesiredState($desired);
$after = phase3c17Materialize($tabList, $desired);

if ($options['dryRun'] !== true) {
    if ($options['snapshot'] === '') {
        throw new \RuntimeException('A --snapshot path is required before navigation mutation.');
    }
    phase3c17WriteSnapshot((string) $options['snapshot'], $tabList);

    if ($after !== $tabList) {
        $configWriter->set('tabList', $after);
        $configWriter->save();
    }
}

echo 'PHASE3C17_NAVIGATION_AFTER ' .
    json_encode($after, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR) .
    PHP_EOL;
echo 'PHASE3C17_NAVIGATION_READY ' . PHASE3C17_NAVIGATION_MARKER .
    ($options['dryRun'] === true ? ' DRY_RUN' : '') .
    PHP_EOL;
