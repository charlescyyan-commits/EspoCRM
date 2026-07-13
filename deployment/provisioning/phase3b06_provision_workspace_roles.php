<?php
/**
 * Phase3B06 — Prospecting Workspace role visibility + dashlet deployment.
 *
 * Idempotent. Extends Sales field ACL to hide technical sync identifiers and
 * deploys the native Prospecting Intelligence dashlet to admin + sales_test.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$container = $app->getContainer();
$em = $container->get('entityManager');
$passwordHash = $container->get('passwordHash');

$SYNC_FIELDS = [
    'peSyncStatus',
    'peSourceSystem',
    'peCandidateId',
    'peLastSyncAt',
    'peEngineVersion',
    'peScoreRulesVersion',
    'peSourceBatchId',
];
$AI_FIELDS = [
    'peOpportunityScoreV4',
    'peScoreTier',
    'peBestFirstProduct',
    'peConfidence',
    'peEvidenceCoverage',
    'peQualificationStatus',
    'peProposalProductFitScore',
    'peProposalCooperationType',
    'peProposalSuggestedNextAction',
    'peProposalEligibility',
    'peProposalAction',
];
$RESEARCH_FIELDS = [
    'peResearchStatus',
    'peResearchSummary',
    'peKeyEvidence',
    'peRecommendedApproach',
    'peLastResearchedAt',
];
$EMAIL_FIELDS = [
    'peEmailStatus',
    'peLastEmailDate',
    'peEmailCampaignName',
    'peEmailReplyStatus',
];

function salesLeadFieldData(array $sync, array $ai, array $research, array $email): array
{
    $fd = [];
    foreach ($sync as $f) {
        $fd[$f] = ['read' => 'no', 'edit' => 'no'];
    }
    foreach (array_merge($ai, $research, $email) as $f) {
        $fd[$f] = ['read' => 'yes', 'edit' => 'no'];
    }
    return $fd;
}

$salesLeadFieldData = salesLeadFieldData($SYNC_FIELDS, $AI_FIELDS, $RESEARCH_FIELDS, $EMAIL_FIELDS);

function upsertRole($em, string $name, array $data, array $fieldData, array $flags = []): string
{
    $role = $em->getRDBRepository('Role')->where(['name' => $name])->findOne();
    if (!$role) {
        $role = $em->getEntity('Role');
        $role->set('name', $name);
    }
    $role->set('data', $data);
    $role->set('fieldData', $fieldData);
    foreach ($flags as $k => $v) {
        $role->set($k, $v);
    }
    $em->saveEntity($role);
    return $role->getId();
}

$salesRoleId = upsertRole(
    $em,
    'Sales User',
    [
        'Lead' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
        'Opportunity' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
        'Account' => ['create' => 'no', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
        'Contact' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no', 'stream' => 'own'],
        'Task' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'own', 'stream' => 'own'],
        'Meeting' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
        'Call' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
        'Note' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'own'],
        'ResearchEvidence' => ['create' => 'no', 'read' => 'own', 'edit' => 'no', 'delete' => 'no'],
        'EmailEvent' => ['create' => 'no', 'read' => 'own', 'edit' => 'no', 'delete' => 'no'],
        'SalesFeedback' => ['create' => 'yes', 'read' => 'own', 'edit' => 'own', 'delete' => 'no'],
        'LearningSignal' => ['create' => 'no', 'read' => 'own', 'edit' => 'no', 'delete' => 'no'],
    ],
    ['Lead' => $salesLeadFieldData],
    ['exportPermission' => 'no', 'massUpdatePermission' => 'no', 'assignmentPermission' => 'no']
);
echo "ROLE_OK Sales User {$salesRoleId}\n";

$researchRoleId = upsertRole(
    $em,
    'Research User',
    [
        'Lead' => ['create' => 'no', 'read' => 'all', 'edit' => 'no', 'delete' => 'no', 'stream' => 'all'],
        'ResearchEvidence' => ['create' => 'yes', 'read' => 'all', 'edit' => 'all', 'delete' => 'no'],
        'EmailEvent' => ['create' => 'no', 'read' => 'all', 'edit' => 'no', 'delete' => 'no'],
        'Task' => ['create' => 'no', 'read' => 'all', 'edit' => 'no', 'delete' => 'no'],
        'Note' => ['create' => 'yes', 'read' => 'all', 'edit' => 'own', 'delete' => 'no'],
    ],
    [
        'Lead' => array_merge(
            salesLeadFieldData($SYNC_FIELDS, $AI_FIELDS, $RESEARCH_FIELDS, $EMAIL_FIELDS),
            [
                'peResearchSummary' => ['read' => 'yes', 'edit' => 'yes'],
                'peKeyEvidence' => ['read' => 'yes', 'edit' => 'yes'],
                'peRecommendedApproach' => ['read' => 'yes', 'edit' => 'yes'],
                'peLastResearchedAt' => ['read' => 'yes', 'edit' => 'yes'],
            ]
        ),
    ],
    ['exportPermission' => 'no', 'massUpdatePermission' => 'no', 'assignmentPermission' => 'no']
);
echo "ROLE_OK Research User {$researchRoleId}\n";

$team = $em->getRDBRepository('Team')->where(['name' => 'Sales Team'])->findOne();
if (!$team) {
    $team = $em->getEntity('Team');
    $team->set('name', 'Sales Team');
    $em->saveEntity($team);
}
$teamId = $team->getId();

$salesUser = $em->getRDBRepository('User')->where(['userName' => 'sales_test'])->findOne();
if (!$salesUser) {
    $salesUser = $em->getEntity('User');
    $salesUser->set('userName', 'sales_test');
    $salesUser->set('firstName', 'Sales');
    $salesUser->set('lastName', 'Test');
    $salesUser->set('type', 'regular');
}
$salesUser->set('isActive', true);
$salesUser->set('password', $passwordHash->hash('SalesTest#2026'));
$salesUser->set('defaultTeamId', $teamId);
$em->saveEntity($salesUser);
$em->getRDBRepository('User')->getRelation($salesUser, 'roles')->relateById($salesRoleId);
$em->getRDBRepository('User')->getRelation($salesUser, 'teams')->relateById($teamId);
echo "USER_OK sales_test {$salesUser->getId()}\n";

$researchUser = $em->getRDBRepository('User')->where(['userName' => 'research_test'])->findOne();
if (!$researchUser) {
    $researchUser = $em->getEntity('User');
    $researchUser->set('userName', 'research_test');
    $researchUser->set('firstName', 'Research');
    $researchUser->set('lastName', 'Test');
    $researchUser->set('type', 'regular');
}
$researchUser->set('isActive', true);
$researchUser->set('password', $passwordHash->hash('ResearchTest#2026'));
$researchUser->set('defaultTeamId', $teamId);
$em->saveEntity($researchUser);
$em->getRDBRepository('User')->getRelation($researchUser, 'roles')->relateById($researchRoleId);
$em->getRDBRepository('User')->getRelation($researchUser, 'teams')->relateById($teamId);
echo "USER_OK research_test {$researchUser->getId()}\n";

function deployProspectingDashlet($em, string $userId): void
{
    $prefs = $em->getEntityById('Preferences', $userId);
    if (!$prefs) {
        $prefs = $em->getEntity('Preferences');
        $prefs->set('id', $userId);
        $prefs->id = $userId;
    }

    $layoutRaw = $prefs->get('dashboardLayout');
    $layout = json_decode(json_encode($layoutRaw), true);
    if (!is_array($layout) || $layout === []) {
        $layout = [[
            'name' => 'My Espo',
            'layout' => [],
        ]];
    }

    $dashletId = 'prospecting-intelligence';
    $found = false;
    foreach ($layout as &$tab) {
        if (!isset($tab['layout']) || !is_array($tab['layout'])) {
            $tab['layout'] = [];
        }
        foreach ($tab['layout'] as $item) {
            if (($item['id'] ?? null) === $dashletId) {
                $found = true;
                break 2;
            }
        }
    }
    unset($tab);

    if (!$found) {
        if (!isset($layout[0]['layout']) || !is_array($layout[0]['layout'])) {
            $layout[0]['layout'] = [];
        }
        $layout[0]['layout'][] = [
            'id' => $dashletId,
            'name' => 'ProspectingIntelligence',
            'x' => 0,
            'y' => 0,
            'width' => 2,
            'height' => 2,
        ];
    }

    $optionsRaw = $prefs->get('dashletsOptions');
    $options = json_decode(json_encode($optionsRaw ?: new stdClass()), true);
    if (!is_array($options)) {
        $options = [];
    }
    $options[$dashletId] = [
        'title' => 'Prospecting Intelligence',
        'entityType' => 'Lead',
        'orderBy' => 'peOpportunityScoreV4',
        'order' => 'desc',
        'displayRecords' => 10,
        'includeShared' => true,
        'expandedLayout' => [
            'rows' => [
                [
                    ['name' => 'name', 'link' => true],
                    ['name' => 'peOpportunityScoreV4'],
                ],
                [
                    ['name' => 'peBestFirstProduct'],
                    ['name' => 'peResearchStatus', 'soft' => true, 'small' => true],
                ],
            ],
        ],
    ];

    $prefs->set('dashboardLayout', $layout);
    $prefs->set('dashletsOptions', $options);
    $em->saveEntity($prefs);
}

$admin = $em->getRDBRepository('User')->where(['userName' => 'admin'])->findOne();
if ($admin) {
    deployProspectingDashlet($em, $admin->getId());
    echo "DASHLET_OK admin\n";
}
deployProspectingDashlet($em, $salesUser->getId());
echo "DASHLET_OK sales_test\n";

echo "PHASE3B06_WORKSPACE_ROLES_DONE\n";
