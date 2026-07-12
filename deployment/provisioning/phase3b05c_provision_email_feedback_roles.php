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
        'SalesFeedback' => permission('yes', 'all', 'all', 'all'),
        'LearningSignal' => permission('yes', 'all', 'all', 'all'),
        'EmailEvent' => permission('yes', 'all', 'all', 'all'),
    ],
    'Sales User' => [
        'SalesFeedback' => permission('yes', 'own', 'own', 'no'),
        'LearningSignal' => permission('no', 'own', 'no', 'no'),
        'EmailEvent' => permission('no', 'own', 'no', 'no'),
    ],
    'Research User' => [
        'SalesFeedback' => permission('no', 'all', 'no', 'no'),
        'LearningSignal' => permission('no', 'all', 'no', 'no'),
        'EmailEvent' => permission('no', 'all', 'no', 'no'),
    ],
    'Integration Bot' => [
        'SalesFeedback' => permission('yes', 'all', 'all', 'no'),
        'LearningSignal' => permission('no', 'all', 'no', 'no'),
        'EmailEvent' => permission('yes', 'all', 'all', 'no'),
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
$user = $entityManager->getRDBRepository('User')->where(['userName' => 'phase3b05c_feedback_test'])->findOne();
if (!$user) {
    $user = $entityManager->getEntity('User');
    $user->set('userName', 'phase3b05c_feedback_test');
}
$user->set('lastName', 'Phase3B05C Feedback Test');
$user->set('type', 'api');
$user->set('isActive', true);
$user->set('authMethod', 'ApiKey');
$user->set('apiKey', 'phase3b05c-local-feedback-test-key');
$entityManager->saveEntity($user);

$relation = $entityManager->getRDBRepository('User')->getRelation($user, 'roles');
if (!$relation->where(['id' => $role->getId()])->findOne()) {
    $relation->relateById($role->getId());
}

echo "PHASE3B05C_FEEDBACK_TEST_USER_READY\n";
