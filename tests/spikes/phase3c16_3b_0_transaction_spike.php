<?php

declare(strict_types=1);

/**
 * Phase3C16.3B-0 isolated runtime spike.
 *
 * Run inside the pinned EspoCRM 10.0.1 application container:
 * php /tmp/phase3c16_3b_0_transaction_spike.php
 *
 * The spike uses native Task entities only as disposable transaction probes.
 * Every committed probe is removed by ID in finally; no Prospecting service,
 * workflow, metadata, or production record is modified.
 */

require '/var/www/html/bootstrap.php';

use Espo\Core\Application;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\TransactionManager;

$application = new Application();
$application->setupSystemUser();

/** @var EntityManager $entityManager */
$entityManager = $application->getContainer()->get('entityManager');
/** @var TransactionManager $transactionManager */
$transactionManager = $entityManager->getTransactionManager();
$pdo = $entityManager->getPDO();
$probeIds = [];
$result = [
    'environment' => [
        'php' => PHP_VERSION,
        'driver' => $pdo->getAttribute(PDO::ATTR_DRIVER_NAME),
        'transactionManager' => TransactionManager::class,
    ],
    'cases' => [],
];

$assert = static function (bool $condition, string $message): void {
    if (!$condition) {
        throw new RuntimeException($message);
    }
};

$createProbe = static function (string $case) use ($entityManager, &$probeIds): string {
    $probe = $entityManager->getNewEntity('Task');
    $probe->set('name', 'C16.3B-0 TX SPIKE ' . $case . ' ' . bin2hex(random_bytes(8)));
    $entityManager->saveEntity($probe);

    $id = (string) $probe->getId();
    if ($id === '') {
        throw new RuntimeException("{$case}: Task probe did not receive an id.");
    }
    $probeIds[] = $id;

    return $id;
};

$persisted = static function (string $id) use ($entityManager): bool {
    return $entityManager->getRDBRepository('Task')->where(['id' => $id])->count() === 1;
};

try {
    // Case 1: inner succeeds and the outer transaction commits.
    $caseOneId = $transactionManager->run(
        static function () use ($transactionManager, $createProbe, $assert): string {
            $assert($transactionManager->getLevel() === 1, 'case-1: outer level must be 1.');
            $assert($transactionManager->isStarted(), 'case-1: outer transaction must be started.');

            $id = $transactionManager->run(
                static function () use ($transactionManager, $createProbe, $assert): string {
                    $assert($transactionManager->getLevel() === 2, 'case-1: inner level must be 2.');

                    return $createProbe('outer-commit');
                }
            );

            $assert($transactionManager->getLevel() === 1, 'case-1: inner commit must restore outer level.');

            return $id;
        }
    );
    $assert($transactionManager->getLevel() === 0, 'case-1: outer commit must restore level 0.');
    $assert(!$transactionManager->isStarted(), 'case-1: transaction must be closed after outer commit.');
    $assert($persisted($caseOneId), 'case-1: committed inner entity write is missing.');
    $result['cases']['outer_commit_after_inner_success'] = ['persisted' => true, 'id' => $caseOneId];

    // Case 2: inner rollback is caught by the outer callback; outer work can commit.
    $caseTwoInnerId = '';
    $caseTwo = $transactionManager->run(
        static function () use ($transactionManager, $createProbe, $assert, &$caseTwoInnerId): array {
            $rolledBackId = '';
            try {
                $transactionManager->run(
                    static function () use ($transactionManager, $createProbe, $assert, &$caseTwoInnerId): string {
                        $assert($transactionManager->getLevel() === 2, 'case-2: inner level must be 2.');
                        $caseTwoInnerId = $createProbe('inner-rollback');
                        throw new RuntimeException('case-2 intentional inner failure');
                    }
                );
            } catch (RuntimeException $exception) {
                $assert($exception->getMessage() === 'case-2 intentional inner failure', 'case-2: unexpected inner exception.');
                $assert($transactionManager->getLevel() === 1, 'case-2: inner rollback must restore outer level.');
                $rolledBackId = $transactionManager->getLevel() === 1 ? $createProbe('outer-after-inner-rollback') : '';
            }

            return ['rolledBackId' => $rolledBackId];
        }
    );
    // The first ID in case 2 is captured by the deterministic name lookup below.
    $caseTwoOuterId = $caseTwo['rolledBackId'];
    $assert($transactionManager->getLevel() === 0, 'case-2: outer commit must restore level 0.');
    $assert(!$persisted($caseTwoInnerId), 'case-2: rolled-back inner entity write persisted.');
    $assert($persisted($caseTwoOuterId), 'case-2: outer entity write after inner rollback is missing.');
    $result['cases']['inner_failure_savepoint_rollback'] = [
        'innerPersisted' => false,
        'outerPersisted' => true,
        'innerId' => $caseTwoInnerId,
        'outerId' => $caseTwoOuterId,
    ];

    // Case 3: releasing the inner savepoint must not leak data when the outer rolls back.
    $caseThreeId = '';
    try {
        $transactionManager->run(
            static function () use ($transactionManager, $createProbe, $assert, &$caseThreeId): void {
                $caseThreeId = $transactionManager->run(
                    static function () use ($transactionManager, $createProbe, $assert): string {
                        $assert($transactionManager->getLevel() === 2, 'case-3: inner level must be 2.');

                        return $createProbe('outer-rollback');
                    }
                );
                $assert($transactionManager->getLevel() === 1, 'case-3: inner success must restore outer level.');
                throw new RuntimeException('case-3 intentional outer failure');
            }
        );
    } catch (RuntimeException $exception) {
        $assert($exception->getMessage() === 'case-3 intentional outer failure', 'case-3: unexpected outer exception.');
    }
    $assert($transactionManager->getLevel() === 0, 'case-3: outer rollback must restore level 0.');
    $assert(!$persisted($caseThreeId), 'case-3: inner entity write leaked after outer rollback.');
    $result['cases']['outer_rollback_after_inner_success'] = ['persisted' => false, 'id' => $caseThreeId];

    $result['decision'] = 'NESTED_TRANSACTION_SUPPORTED';
} finally {
    foreach (array_unique($probeIds) as $probeId) {
        $probe = $entityManager->getEntityById('Task', $probeId);
        if ($probe instanceof Entity) {
            $entityManager->removeEntity($probe);
        }
    }

    $remainingProbeIds = array_values(array_filter($probeIds, $persisted));
    $result['cleanup'] = [
        'remainingProbeCount' => count($remainingProbeIds),
        'complete' => $remainingProbeIds === [],
    ];
}

if (($result['cleanup']['complete'] ?? false) !== true) {
    throw new RuntimeException('Spike cleanup left persisted Task probes.');
}

echo json_encode($result, JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR) . PHP_EOL;
