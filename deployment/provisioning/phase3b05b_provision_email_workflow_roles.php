<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

function permission(string $create, string $read, string $edit, string $delete, string $stream = 'no'): array
{
    return compact('create', 'read', 'edit', 'delete', 'stream');
}

$rolePermissions = [
    'Admin' => [
        'EmailEvent' => permission('yes', 'all', 'all', 'all'),
        'Task' => permission('yes', 'all', 'all', 'all'),
    ],
    'Sales User' => [
        'EmailEvent' => permission('no', 'own', 'no', 'no'),
        'Task' => permission('yes', 'own', 'own', 'own'),
    ],
    'Research User' => [
        'EmailEvent' => permission('no', 'all', 'no', 'no'),
        'Task' => permission('no', 'own', 'no', 'no'),
    ],
    'Integration Bot' => [
        'EmailEvent' => permission('yes', 'all', 'all', 'no'),
        'Task' => permission('no', 'no', 'no', 'no'),
    ],
];

foreach ($rolePermissions as $roleName => $permissions) {
    $role = $entityManager->getRDBRepository('Role')->where(['name' => $roleName])->findOne();
    if (!$role) {
        throw new \RuntimeException("Required role is missing: {$roleName}.");
    }
    $data = $role->get('data') ?: [];
    if ($data instanceof \stdClass) {
        $data = (array) $data;
    }
    foreach ($permissions as $entityType => $entityPermission) {
        $data[$entityType] = $entityPermission;
    }
    $role->set('data', $data);
    $entityManager->saveEntity($role);
    echo "ROLE_OK {$roleName}\n";
}

$role = $entityManager->getRDBRepository('Role')->where(['name' => 'Integration Bot'])->findOne();
$user = $entityManager->getRDBRepository('User')->where(['userName' => 'phase3b05b_workflow_test'])->findOne();
if (!$user) {
    $user = $entityManager->getEntity('User');
    $user->set('userName', 'phase3b05b_workflow_test');
}
$user->set('lastName', 'Phase3B05B Workflow Test');
$user->set('type', 'api');
$user->set('isActive', true);
$user->set('authMethod', 'ApiKey');
$user->set('apiKey', 'phase3b05b-local-workflow-test-key');
$entityManager->saveEntity($user);

$relation = $entityManager->getRDBRepository('User')->getRelation($user, 'roles');
if (!$relation->where(['id' => $role->getId()])->findOne()) {
    $relation->relateById($role->getId());
}

echo "PHASE3B05B_WORKFLOW_TEST_USER_READY\n";
