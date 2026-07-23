<?php

declare(strict_types=1);

/**
 * Deprecated compatibility entry point.
 *
 * U04 is no longer an independent config.tabList writer. It delegates to the
 * canonical Phase3C17 materializer and therefore cannot restore or overwrite
 * the C17 desired navigation with the obsolete U04 list.
 */

fwrite(
    STDERR,
    'DEPRECATED: use phase3c17_provision_operational_centers_navigation.php directly.' . PHP_EOL
);

require __DIR__ . '/phase3c17_provision_operational_centers_navigation.php';
