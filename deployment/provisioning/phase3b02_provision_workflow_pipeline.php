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

// ── Phase3B02 ACL Matrix ──────────────────────────────────────────────
//
// Admin:    Full access (Lead, ResearchEvidence, Opportunity, Task)
// Sales:    Lead (create/read/edit own), Read all ResearchEvidence,
//           Opportunity (create/read/edit own), Task (create/read own)
// Research: Lead (read all, no edit), ResearchEvidence (create/read/edit all, no delete),
//           Opportunity (no access), Task (no access)

$adminRole = upsertRole($entityManager, 'Admin', [
    'Lead'             => entityPermission('yes', 'all', 'all', 'all', 'all'),
    'ResearchEvidence' => entityPermission('yes', 'all', 'all', 'all'),
    'Opportunity'      => entityPermission('yes', 'all', 'all', 'all', 'all'),
    'Task'             => entityPermission('yes', 'all', 'all', 'all', 'all'),
]);

$salesRole = upsertRole($entityManager, 'Sales User', [
    'Lead'             => entityPermission('yes', 'own', 'own', 'no', 'own'),
    'ResearchEvidence' => entityPermission('no', 'all', 'no', 'no'),
    'Opportunity'      => entityPermission('yes', 'own', 'own', 'no', 'own'),
    'Task'             => entityPermission('yes', 'own', 'own', 'no', 'own'),
]);

$researchRole = upsertRole($entityManager, 'Research User', [
    'Lead'             => entityPermission('no', 'all', 'no', 'no'),
    'ResearchEvidence' => entityPermission('yes', 'all', 'all', 'no'),
    'Opportunity'      => entityPermission('no', 'no', 'no', 'no'),
    'Task'             => entityPermission('no', 'no', 'no', 'no'),
]);

// ── Verify test users exist ────────────────────────────────────────────

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

// ── Verify pipeline metadata ──────────────────────────────────────────

$leadDefs = $entityManager->getMetadata()->get('entityDefs.Lead');
$outreachStatusField = $leadDefs['fields']['outreachStatus'] ?? null;
if ($outreachStatusField && ($outreachStatusField['options'] ?? []) === [
    'NEW', 'RESEARCHING', 'RESEARCH_COMPLETED', 'QUALIFIED',
    'CONTACT_READY', 'CONTACTED', 'RESPONDED', 'CONVERTED', 'CLOSED_LOST',
]) {
    echo "PIPELINE_OK outreachStatus\n";
} else {
    echo "PIPELINE_FAIL outreachStatus\n";
}

$formula = $leadDefs['formula'] ?? '';
if (!empty($formula) && strpos($formula, 'CONTACT_READY') !== false) {
    echo "FORMULA_OK Lead formula present\n";
} else {
    echo "FORMULA_FAIL Lead formula missing or incomplete\n";
}

$oppStageDefs = $entityManager->getMetadata()->get('entityDefs.Opportunity.fields.stage');
if ($oppStageDefs && ($oppStageDefs['options'] ?? []) === [
    'DISCOVERY', 'QUALIFICATION', 'CONTACTED', 'NEGOTIATION', 'WON', 'LOST',
]) {
    echo "PIPELINE_OK Opportunity stage\n";
} else {
    echo "PIPELINE_FAIL Opportunity stage\n";
}

echo "PHASE3B02_WORKFLOW_PIPELINE_ACL_DONE\n";
