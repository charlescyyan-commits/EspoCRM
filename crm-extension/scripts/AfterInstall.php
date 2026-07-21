<?php

declare(strict_types=1);

use Espo\Core\Container;
use Espo\ORM\EntityManager;

/**
 * Provisions extension-owned schema before any Quote workflow request runs.
 */
class AfterInstall
{
    public function run(Container $container): void
    {
        $container->getByClass(EntityManager::class)->getPDO()->exec(
            'CREATE TABLE IF NOT EXISTS numbering_sequence (' .
            'sequence_key VARCHAR(64) NOT NULL PRIMARY KEY, ' .
            'current_value INT UNSIGNED NOT NULL DEFAULT 0, ' .
            'updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' .
            ') ENGINE=InnoDB'
        );
    }
}
