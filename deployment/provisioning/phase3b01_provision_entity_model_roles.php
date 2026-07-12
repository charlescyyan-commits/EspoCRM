<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$container = $app->getContainer();
$entityManager = $container->get('entityManager');
$passwordHash = $container->get('passwordHash');

function entityPermission(string $create, string $read, string $edit, string $delete, string $stream = 'no'): array
{
    return [
        'create' => $create,
        'read' => $read,
        'edit' => $edit,
        'delete' => $delete,
        'stream' => $stream,
    ];
}

function upsertRole($entityManager, string $name, array $entityPermissions): object
{
    $role = $entityManager->getRDBRepository('Role')->where(['name' => $name])->findOne();
    if (!$role) {
        $role = $entityManager->getEntity('Role');
        $role->set('name', $name);
    }

    $data = $role->get('data') ?: [];
    if ($data instanceof \stdClass) {
        $data = (array) $data;
    }
    foreach ($entityPermissions as $entityType => $permission) {
        $data[$entityType] = $permission;
    }
    $role->set('data', $data);
    $entityManager->saveEntity($role);

    return $role;
}

function relateRoleOnce($entityManager, $user, string $roleId): void
{
    $relation = $entityManager->getRDBRepository('User')->getRelation($user, 'roles');
    if (!$relation->where(['id' => $roleId])->findOne()) {
        $relation->relateById($roleId);
    }
}

$adminRole = upsertRole($entityManager, 'Admin', [
    'Lead' => entityPermission('yes', 'all', 'all', 'all', 'all'),
    'ResearchEvidence' => entityPermission('yes', 'all', 'all', 'all'),
    'Opportunity' => entityPermission('yes', 'all', 'all', 'all', 'all'),
]);

$salesRole = upsertRole($entityManager, 'Sales User', [
    'Lead' => entityPermission('yes', 'own', 'own', 'no', 'own'),
    'ResearchEvidence' => entityPermission('no', 'all', 'no', 'no'),
    'Opportunity' => entityPermission('yes', 'own', 'own', 'no', 'own'),
]);

$researchRole = upsertRole($entityManager, 'Research User', [
    'Lead' => entityPermission('no', 'all', 'no', 'no'),
    'ResearchEvidence' => entityPermission('yes', 'all', 'all', 'no'),
    'Opportunity' => entityPermission('no', 'no', 'no', 'no'),
]);

$researchUser = $entityManager->getRDBRepository('User')->where(['userName' => 'research_test'])->findOne();
if (!$researchUser) {
    $researchUser = $entityManager->getEntity('User');
    $researchUser->set('userName', 'research_test');
}
$researchUser->set('firstName', 'Research');
$researchUser->set('lastName', 'Test');
$researchUser->set('type', 'regular');
$researchUser->set('isActive', true);
$researchUser->set('password', $passwordHash->hash('ResearchTest#2026'));
$entityManager->saveEntity($researchUser);
relateRoleOnce($entityManager, $researchUser, $researchRole->getId());

echo "ROLE_OK Admin {$adminRole->getId()}\n";
echo "ROLE_OK Sales User {$salesRole->getId()}\n";
echo "ROLE_OK Research User {$researchRole->getId()}\n";
echo "USER_OK research_test {$researchUser->getId()}\n";
echo "PHASE3B01_ENTITY_MODEL_ACL_DONE\n";
