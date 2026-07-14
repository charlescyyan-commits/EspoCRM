<?php

/**
 * Phase ACL03 — Sales Manager Lead field-visibility convergence.
 *
 * Updates only the existing Sales Manager role's Lead fieldData. Entity ACL,
 * other roles, user relationships, workflows, and application logic are left
 * untouched. The operation is idempotent.
 *
 * Run as the EspoCRM system user:
 *   docker cp deployment/provisioning/phase_acl03_apply_sales_manager_field_visibility.php espocrm:/tmp/
 *   docker exec espocrm php /tmp/phase_acl03_apply_sales_manager_field_visibility.php
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$hiddenFields = [
    'peSyncStatus',
    'peSourceSystem',
    'peCandidateId',
    'peLastSyncAt',
    'peEngineVersion',
    'peScoreRulesVersion',
    'peSourceBatchId',
];

$readOnlyFields = [
    'peOpportunityScoreV4',
    'peScoreTier',
    'peBestFirstProduct',
    'peResearchStatus',
    'peEmailStatus',
    'peLastEmailDate',
    'peEmailCampaignName',
    'peEmailReplyStatus',
    'peSourceType',
    'peDiscoverySource',
    'peCompanyType',
    'peIndustry',
    'peBusinessModel',
    'pePriorityLevel',
    'peLastResearchedAt',
    'peProposalProductFitScore',
    'peProposalCooperationType',
    'peProposalSuggestedNextAction',
    'peProposalEligibility',
    'peProposalAction',
    'peContactFormUrl',
    'peLinkedinUrl',
    'peResearchSummary',
    'peKeyEvidence',
    'peRecommendedApproach',
    'peConfidence',
    'peEvidenceCoverage',
    'peQualificationStatus',
];

// CRM-owned sales activity fields intentionally remain governed by Lead.edit=team.
$editableFields = ['peNextActionDate', 'peLastContactDate'];

$role = $entityManager->getRDBRepository('Role')
    ->where(['name' => 'Sales Manager'])
    ->findOne();

if (!$role) {
    throw new \RuntimeException('Sales Manager role was not found.');
}

$fieldData = (array) ($role->get('fieldData') ?? []);
$leadFieldData = (array) ($fieldData['Lead'] ?? []);

foreach ($hiddenFields as $field) {
    $leadFieldData[$field] = ['read' => 'no', 'edit' => 'no'];
}

foreach ($readOnlyFields as $field) {
    $leadFieldData[$field] = ['read' => 'yes', 'edit' => 'no'];
}

foreach ($editableFields as $field) {
    unset($leadFieldData[$field]);
}

$fieldData['Lead'] = $leadFieldData;
$role->set('fieldData', $fieldData);
$entityManager->saveEntity($role);

$persistedRole = $entityManager->getRDBRepository('Role')
    ->where(['name' => 'Sales Manager'])
    ->findOne();
$persistedFieldData = (array) ($persistedRole->get('fieldData') ?? []);
$persistedLeadFieldData = (array) ($persistedFieldData['Lead'] ?? []);
$validationFailures = [];

foreach ($hiddenFields as $field) {
    $rule = (array) ($persistedLeadFieldData[$field] ?? []);
    if (($rule['read'] ?? null) !== 'no' || ($rule['edit'] ?? null) !== 'no') {
        $validationFailures[] = $field;
    }
}

foreach ($readOnlyFields as $field) {
    $rule = (array) ($persistedLeadFieldData[$field] ?? []);
    if (($rule['read'] ?? null) !== 'yes' || ($rule['edit'] ?? null) !== 'no') {
        $validationFailures[] = $field;
    }
}

foreach ($editableFields as $field) {
    if (array_key_exists($field, $persistedLeadFieldData)) {
        $validationFailures[] = $field;
    }
}

if ($validationFailures) {
    throw new \RuntimeException('ACL03 persistence validation failed: ' . implode(',', $validationFailures));
}

echo sprintf(
    "ACL03_OK roleId=%s hidden=%d readOnly=%d editable=%s\n",
    $role->getId(),
    count($hiddenFields),
    count($readOnlyFields),
    implode(',', $editableFields)
);
