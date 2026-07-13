<?php
/**
 * Phase3B06 — Create a controlled synthetic Lead for browser UI verification.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$em = $app->getContainer()->get('entityManager');

$salesUser = $em->getRDBRepository('User')->where(['userName' => 'sales_test'])->findOne();
$assignedUserId = $salesUser ? $salesUser->getId() : null;

$existing = $em->getRDBRepository('Lead')
    ->where(['name' => 'PHASE3B06-TEST Workspace Co'])
    ->findOne();
if ($existing) {
    $lead = $existing;
} else {
    $lead = $em->getEntity('Lead');
}

$lead->set([
    'name' => 'PHASE3B06-TEST Workspace Co',
    'lastName' => 'PHASE3B06-TEST Workspace Co',
    'website' => 'https://phase3b06-test.example',
    'addressCountry' => 'Singapore',
    'emailAddress' => 'workspace@phase3b06-test.example',
    'status' => 'New',
    'peOpportunityScoreV4' => 88.5,
    'peScoreTier' => 'A',
    'peBestFirstProduct' => 'Chitu Intelligence Suite',
    'peResearchStatus' => 'COMPLETED',
    'peSourceType' => 'AI_DISCOVERY',
    'peDiscoverySource' => 'Phase3B06 synthetic',
    'pePriorityLevel' => 'HIGH',
    'peCompanyType' => 'Distributor',
    'peIndustry' => 'Industrial Automation',
    'peBusinessModel' => 'B2B',
    'outreachStatus' => 'CONTACT_READY',
    'peEmailStatus' => 'SENT',
    'peLastEmailDate' => date('Y-m-d H:i:s', strtotime('-2 days')),
    'peEmailCampaignName' => 'PHASE3B06-WORKSPACE',
    'peLastResearchedAt' => date('Y-m-d H:i:s', strtotime('-1 day')),
    'peResearchSummary' => 'Synthetic research summary for Prospecting Workspace UI verification.',
    'peKeyEvidence' => 'Public product page mentions automation sourcing.',
    'peRecommendedApproach' => 'Lead with distributor partnership angle.',
    'peConfidence' => 0.86,
    'peEvidenceCoverage' => 0.72,
    'peProposalProductFitScore' => 88.5,
    'peProposalCooperationType' => 'DISTRIBUTOR',
    'peProposalSuggestedNextAction' => 'Manual opportunity review',
    'peProposalEligibility' => true,
    'peProposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
    'peSyncStatus' => 'SYNCED',
    'peSourceSystem' => 'CHITU',
    'peCandidateId' => 'phase3b06-synthetic-candidate',
    'peSourceBatchId' => 'phase3b06-batch',
    'peLastSyncAt' => date('Y-m-d H:i:s'),
    'peEngineVersion' => 'test-engine',
    'peScoreRulesVersion' => 'v4-test',
    'assignedUserId' => $assignedUserId,
]);
$em->saveEntity($lead);
$leadId = $lead->getId();
echo "LEAD_OK {$leadId}\n";

$evidence = $em->getRDBRepository('ResearchEvidence')
    ->where(['peEvidenceId' => 'phase3b06-evidence-1'])
    ->findOne();
if (!$evidence) {
    $evidence = $em->getEntity('ResearchEvidence');
}
$evidence->set([
    'name' => 'Automation product page',
    'peEvidenceId' => 'phase3b06-evidence-1',
    'peClaim' => 'Company sells industrial automation components',
    'peClaimType' => 'PRODUCT',
    'peEvidenceType' => 'WEB_PAGE',
    'peSourceUrl' => 'https://phase3b06-test.example/products',
    'peEvidenceText' => 'Catalog lists PLC and motion control products.',
    'peContentSummary' => 'Public catalog confirms automation product focus.',
    'peConfidence' => 0.91,
    'peCapturedAt' => date('Y-m-d H:i:s', strtotime('-1 day')),
    'peSchemaVersion' => '1.0',
    'leadId' => $leadId,
    'assignedUserId' => $assignedUserId,
]);
$em->saveEntity($evidence);
echo "EVIDENCE_OK {$evidence->getId()}\n";

$emailEvent = $em->getRDBRepository('EmailEvent')
    ->where(['externalMessageId' => 'phase3b06-msg-1', 'eventType' => 'SENT'])
    ->findOne();
if (!$emailEvent) {
    $emailEvent = $em->getEntity('EmailEvent');
}
$emailEvent->set([
    'name' => 'SENT phase3b06-msg-1',
    'externalMessageId' => 'phase3b06-msg-1',
    'eventType' => 'SENT',
    'campaign' => 'PHASE3B06-WORKSPACE',
    'eventAt' => date('Y-m-d H:i:s', strtotime('-2 days')),
    'source' => 'BREVO',
    'leadId' => $leadId,
    'assignedUserId' => $assignedUserId,
]);
$em->saveEntity($emailEvent);
echo "EMAIL_EVENT_OK {$emailEvent->getId()}\n";

$feedback = $em->getRDBRepository('SalesFeedback')
    ->where(['externalFeedbackId' => 'phase3b06-feedback-1'])
    ->findOne();
if (!$feedback) {
    $feedback = $em->getEntity('SalesFeedback');
}
$feedback->set([
    'name' => 'PHASE3B06 feedback',
    'externalFeedbackId' => 'phase3b06-feedback-1',
    'externalLeadId' => 'phase3b06-synthetic-candidate',
    'feedbackType' => 'CONTACT_ATTEMPT',
    'outcome' => 'NEUTRAL',
    'note' => 'Synthetic sales feedback for UI verification',
    'product' => 'Chitu Intelligence Suite',
    'campaign' => 'PHASE3B06-WORKSPACE',
    'source' => 'MANUAL',
    'feedbackAt' => date('Y-m-d H:i:s'),
    'leadId' => $leadId,
    'assignedUserId' => $assignedUserId,
]);
$em->saveEntity($feedback);
echo "FEEDBACK_OK {$feedback->getId()}\n";

echo "PHASE3B06_SYNTHETIC_LEAD_READY\n";
echo "LEAD_ID={$leadId}\n";
