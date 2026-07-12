<?php
/**
 * Phase 3A-33 — Production ACL & Sales Role provisioning.
 *
 * Idempotent. Creates/updates the least-privilege production role model plus a
 * disposable verification Team and Users. Run via the EspoCRM system user:
 *
 *   docker exec espocrm php /tmp/phase3a33_provision_roles.php
 *
 * This is an operational admin script. It is intentionally kept OUTSIDE the
 * deployable extension package (`espocrm_extension/`) so it is never shipped
 * or executed as an EspoCRM install hook.
 *
 * Boundaries:
 *  - Does NOT modify the existing "Chitu Integration Role" (Phase 3A-24 test
 *    rollback foundation). Production integration ACL is delivered as a NEW
 *    "Integration Bot" role with delete denied.
 *  - Does NOT touch scoring engine, email engine, sync architecture or UI.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$container = $app->getContainer();
$em = $container->get('entityManager');
$passwordHash = $container->get('passwordHash');

// --- Field categories (Lead) --------------------------------------------------
$SYNC_FIELDS = ['peSyncStatus', 'peSourceSystem', 'peCandidateId', 'peLastSyncAt', 'peEngineVersion', 'peScoreRulesVersion'];
$AI_FIELDS = ['peOpportunityScoreV4', 'peScoreTier', 'peBestFirstProduct', 'peConfidence', 'peEvidenceCoverage', 'peQualificationStatus'];
$RESEARCH_FIELDS = ['peResearchStatus', 'peResearchSummary', 'peKeyEvidence', 'peRecommendedApproach'];

/** Sales field policy: sync hidden; AI + research read-only. */
function salesLeadFieldData(array $sync, array $ai, array $research): array
{
    $fd = [];
    foreach ($sync as $f) {
        $fd[$f] = ['read' => 'no', 'edit' => 'no'];
    }
    foreach (array_merge($ai, $research) as $f) {
        $fd[$f] = ['read' => 'yes', 'edit' => 'no'];
    }
    return $fd;
}

$salesLeadFieldData = salesLeadFieldData($SYNC_FIELDS, $AI_FIELDS, $RESEARCH_FIELDS);

// --- Role definitions ---------------------------------------------------------
$roles = [
    'Admin' => [
        'data' => [
            'Lead' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all', 'stream' => 'all'],
            'Account' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all', 'stream' => 'all'],
            'Contact' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all', 'stream' => 'all'],
            'Opportunity' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all', 'stream' => 'all'],
            'ResearchEvidence' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
            'Task' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all', 'stream' => 'all'],
            'Meeting' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
            'Call' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
            'Note' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
            'Report' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'all'],
        ],
        'fieldData' => [],
        'flags' => ['exportPermission' => 'yes', 'massUpdatePermission' => 'yes', 'assignmentPermission' => 'all'],
    ],
    'Integration Bot' => [
        'data' => [
            'Lead' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no', 'stream' => 'no'],
            'Account' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no', 'stream' => 'no'],
            'Contact' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no', 'stream' => 'no'],
            'Opportunity' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no', 'stream' => 'no'],
            'ResearchEvidence' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no'],
        ],
        'fieldData' => [],
        'flags' => ['exportPermission' => 'no', 'massUpdatePermission' => 'no', 'assignmentPermission' => 'all'],
    ],
    'Sales User' => [
        'data' => [
            'Lead' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
            'Opportunity' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
            'Account' => ['create' => 'no', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
            'Contact' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
            'Task' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'own', 'stream' => 'own'],
            'Meeting' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
            'Call' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
            'Note' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'own'],
        ],
        'fieldData' => ['Lead' => $salesLeadFieldData],
        'flags' => ['exportPermission' => 'no', 'massUpdatePermission' => 'no', 'assignmentPermission' => 'no'],
    ],
    'Sales Manager' => [
        'data' => [
            'Lead' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no', 'stream' => 'team'],
            'Opportunity' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no', 'stream' => 'team'],
            'Account' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no', 'stream' => 'team'],
            'Contact' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no', 'stream' => 'team'],
            'Task' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no', 'stream' => 'team'],
            'Meeting' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no'],
            'Call' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no'],
            'Note' => ['create' => 'yes', 'read' => 'team', 'edit' => 'team', 'delete' => 'no'],
            'Report' => ['create' => 'no', 'read' => 'all', 'edit' => 'no', 'delete' => 'no'],
        ],
        'fieldData' => ['Lead' => $salesLeadFieldData],
        'flags' => ['exportPermission' => 'team', 'massUpdatePermission' => 'no', 'assignmentPermission' => 'team'],
    ],
];

function upsertRole($em, string $name, array $def): string
{
    $role = $em->getRDBRepository('Role')->where(['name' => $name])->findOne();
    if (!$role) {
        $role = $em->getEntity('Role');
        $role->set('name', $name);
    }
    $role->set('data', $def['data']);
    $role->set('fieldData', $def['fieldData']);
    foreach ($def['flags'] as $k => $v) {
        $role->set($k, $v);
    }
    $em->saveEntity($role);
    return $role->get('id');
}

$roleIds = [];
foreach ($roles as $name => $def) {
    $roleIds[$name] = upsertRole($em, $name, $def);
    echo "ROLE_OK {$name} {$roleIds[$name]}\n";
}

// --- Team ---------------------------------------------------------------------
$teamName = 'Sales Team';
$team = $em->getRDBRepository('Team')->where(['name' => $teamName])->findOne();
if (!$team) {
    $team = $em->getEntity('Team');
    $team->set('name', $teamName);
    $em->saveEntity($team);
}
$teamId = $team->get('id');
echo "TEAM_OK {$teamName} {$teamId}\n";

// --- Users --------------------------------------------------------------------
function upsertUser($em, string $userName, array $attrs): object
{
    $user = $em->getRDBRepository('User')->where(['userName' => $userName])->findOne();
    if (!$user) {
        $user = $em->getEntity('User');
        $user->set('userName', $userName);
    }
    foreach ($attrs as $k => $v) {
        $user->set($k, $v);
    }
    return $user;
}

function relateOnce($em, $entity, string $link, string $foreignId): void
{
    $rel = $em->getRDBRepository($entity->getEntityType())->getRelation($entity, $link);
    $existing = $rel->where(['id' => $foreignId])->findOne();
    if (!$existing) {
        $rel->relateById($foreignId);
    }
}

// Sales User (regular, UI)
$salesUser = upsertUser($em, 'sales_test', [
    'firstName' => 'Sales', 'lastName' => 'Test', 'type' => 'regular', 'isActive' => true,
    'password' => $passwordHash->hash('SalesTest#2026'),
    'defaultTeamId' => $teamId,
]);
$em->saveEntity($salesUser);
relateOnce($em, $salesUser, 'roles', $roleIds['Sales User']);
relateOnce($em, $salesUser, 'teams', $teamId);
echo "USER_OK sales_test {$salesUser->get('id')} pass=SalesTest#2026\n";

// Sales Manager (regular, UI)
$managerUser = upsertUser($em, 'manager_test', [
    'firstName' => 'Manager', 'lastName' => 'Test', 'type' => 'regular', 'isActive' => true,
    'password' => $passwordHash->hash('ManagerTest#2026'),
    'defaultTeamId' => $teamId,
]);
$em->saveEntity($managerUser);
relateOnce($em, $managerUser, 'roles', $roleIds['Sales Manager']);
relateOnce($em, $managerUser, 'teams', $teamId);
echo "USER_OK manager_test {$managerUser->get('id')} pass=ManagerTest#2026\n";

// Integration Bot verification user (api)
$botKey = bin2hex(random_bytes(16));
$botUser = $em->getRDBRepository('User')->where(['userName' => 'integration_bot_test'])->findOne();
$reuseKey = $botUser ? $botUser->get('apiKey') : null;
$botUser = upsertUser($em, 'integration_bot_test', [
    'lastName' => 'Integration Bot Test', 'type' => 'api', 'isActive' => true,
    'authMethod' => 'ApiKey',
    'apiKey' => $reuseKey ?: $botKey,
]);
$em->saveEntity($botUser);
relateOnce($em, $botUser, 'roles', $roleIds['Integration Bot']);
echo "APIUSER_OK integration_bot_test {$botUser->get('id')} apiKey={$botUser->get('apiKey')}\n";

echo "PHASE3A33_PROVISION_DONE\n";
