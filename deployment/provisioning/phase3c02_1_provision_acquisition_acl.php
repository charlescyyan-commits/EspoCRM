<?php

declare(strict_types=1);

require '/var/www/html/bootstrap.php';

$application = new \Espo\Core\Application();
$application->setupSystemUser();
$entityManager = $application->getContainer()->get('entityManager');

$scopePermissions = [
    'Admin' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
    'Sales Manager' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no'],
    'Sales User' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
    'Integration Bot' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no'],
];

$scopeList = ['SearchStrategy', 'SearchJob', 'ProspectPool'];

foreach ($scopePermissions as $roleName => $permissions) {
    $role = $entityManager->getRDBRepository('Role')->where(['name' => $roleName])->findOne();

    if (!$role) {
        throw new \RuntimeException("Required role is missing: {$roleName}.");
    }

    $roleData = json_decode(json_encode($role->get('data') ?: []), true, 512, JSON_THROW_ON_ERROR);

    foreach ($scopeList as $scopeName) {
        $roleData[$scopeName] = $permissions;
    }

    $role->set('data', $roleData);
    $entityManager->saveEntity($role);

    echo "ROLE_OK {$roleName}\n";
}

echo "PHASE3C02_1_ACQUISITION_ACL_DONE\n";
