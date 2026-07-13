<?php

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');

$salesUser = $entityManager->getRDBRepository('User')->where(['userName' => 'sales_test'])->findOne();
$managerUser = $entityManager->getRDBRepository('User')->where(['userName' => 'manager_test'])->findOne();
$salesTeam = $entityManager->getRDBRepository('Team')->where(['name' => 'Sales Team'])->findOne();
if (!$salesUser || !$managerUser || !$salesTeam) {
    throw new \RuntimeException('sales_test, manager_test, and Sales Team are required.');
}

$marker = '[CHITU_PHASE3B07_TEST]';
$now = (new \DateTimeImmutable())->format('Y-m-d H:i:s');
$leadDefinitions = [
    'a-tier' => [
        'label' => 'A-TIER', 'score' => 92.0, 'tier' => 'A', 'research' => 'COMPLETED', 'outreach' => 'QUALIFIED',
        'sync' => 'SYNCED', 'product' => 'Resin Tank', 'summary' => 'Synthetic A-tier research summary.',
        'evidence' => 'Synthetic A-tier evidence.', 'approach' => 'Synthetic A-tier recommended approach.',
        'coverage' => 0.90, 'confidence' => 0.91, 'proposalEligible' => true, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => 'a-tier@phase3b07-test.example', 'website' => 'https://a-tier.phase3b07-test.example',
    ],
    'research-pending' => [
        'label' => 'RESEARCH-PENDING', 'score' => null, 'tier' => null, 'research' => 'RESEARCHING', 'outreach' => 'RESEARCHING',
        'sync' => 'SYNCED', 'product' => null, 'summary' => null, 'evidence' => null, 'approach' => null,
        'coverage' => null, 'confidence' => null, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => 'https://research-pending.phase3b07-test.example',
    ],
    'missing-evidence' => [
        'label' => 'MISSING-EVIDENCE', 'score' => 70.0, 'tier' => 'B', 'research' => 'COMPLETED', 'outreach' => 'RESEARCH_COMPLETED',
        'sync' => 'SYNCED', 'product' => 'Filament Dryer', 'summary' => 'Synthetic completed research without related evidence.',
        'evidence' => null, 'approach' => 'Synthetic missing-evidence approach.',
        'coverage' => 0.50, 'confidence' => 0.70, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => 'https://missing-evidence.phase3b07-test.example',
    ],
    'contact-ready' => [
        'label' => 'CONTACT-READY', 'score' => 78.0, 'tier' => 'B', 'research' => 'COMPLETED', 'outreach' => 'CONTACT_READY',
        'sync' => 'SYNCED', 'product' => 'Resin Tank', 'summary' => 'Synthetic contact-ready research summary.',
        'evidence' => 'Synthetic contact-ready evidence.', 'approach' => 'Synthetic contact-ready approach.',
        'coverage' => 0.80, 'confidence' => 0.82, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => 'contact-ready@phase3b07-test.example', 'website' => 'https://contact-ready.phase3b07-test.example',
    ],
    'sync-failed' => [
        'label' => 'SYNC-FAILED', 'score' => null, 'tier' => null, 'research' => 'FAILED', 'outreach' => 'NEW',
        'sync' => 'FAILED', 'product' => null, 'summary' => null, 'evidence' => null, 'approach' => null,
        'coverage' => null, 'confidence' => null, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => null,
    ],
    'proposal-review' => [
        'label' => 'PROPOSAL-REVIEW', 'score' => 88.0, 'tier' => 'A', 'research' => 'COMPLETED', 'outreach' => 'QUALIFIED',
        'sync' => 'SYNCED', 'product' => 'Resin Tank', 'summary' => 'Synthetic proposal-review research summary.',
        'evidence' => 'Synthetic proposal-review evidence.', 'approach' => 'Synthetic proposal-review approach.',
        'coverage' => 0.88, 'confidence' => 0.90, 'proposalEligible' => true, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => 'https://proposal-review.phase3b07-test.example',
    ],
    'score-without-tier' => [
        'label' => 'SCORE-WITHOUT-TIER', 'score' => 60.0, 'tier' => '', 'research' => 'NONE', 'outreach' => 'NEW',
        'sync' => 'SYNCED', 'product' => '', 'summary' => null, 'evidence' => null, 'approach' => null,
        'coverage' => null, 'confidence' => null, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => 'https://score-without-tier.phase3b07-test.example',
    ],
    'proposal-action-missing' => [
        'label' => 'PROPOSAL-ACTION-MISSING', 'score' => 81.0, 'tier' => 'A', 'research' => 'COMPLETED', 'outreach' => 'QUALIFIED',
        'sync' => 'SYNCED', 'product' => 'Resin Tank', 'summary' => 'Synthetic proposal action quality check.',
        'evidence' => 'Synthetic proposal action evidence.', 'approach' => 'Synthetic proposal action approach.',
        'coverage' => 0.81, 'confidence' => 0.82, 'proposalEligible' => true, 'proposalAction' => '',
        'email' => null, 'website' => 'https://proposal-action.phase3b07-test.example',
    ],
    'contact-ready-no-contact' => [
        'label' => 'CONTACT-READY-NO-CONTACT', 'score' => 75.0, 'tier' => 'B', 'research' => 'COMPLETED', 'outreach' => 'CONTACT_READY',
        'sync' => 'SYNCED', 'product' => 'Filament Dryer', 'summary' => 'Synthetic contact-method quality check.',
        'evidence' => 'Synthetic contact-method evidence.', 'approach' => 'Synthetic contact-method approach.',
        'coverage' => 0.75, 'confidence' => 0.78, 'proposalEligible' => false, 'proposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        'email' => null, 'website' => 'https://contact-ready-no-contact.phase3b07-test.example',
    ],
];

$leads = [];
foreach ($leadDefinitions as $key => $definition) {
    $lead = $entityManager->getEntity('Lead');
    $name = "{$marker} {$definition['label']}";
    $lead->set([
        'name' => $name,
        'lastName' => $name,
        'peCandidateId' => "phase3b07-{$key}",
        'peSourceBatchId' => 'phase3b07-validation',
        'peSourceSystem' => 'Chitu Intelligence',
        'peSourceType' => 'CONTROLLED_MANUAL_INPUT',
        'peDiscoverySource' => 'Phase3B07 local validation',
        'website' => $definition['website'],
        'emailAddress' => $definition['email'],
        'peOpportunityScoreV4' => $definition['score'],
        'peScoreTier' => $definition['tier'],
        'peBestFirstProduct' => $definition['product'],
        'peResearchStatus' => $definition['research'],
        'peResearchSummary' => $definition['summary'],
        'peKeyEvidence' => $definition['evidence'],
        'peRecommendedApproach' => $definition['approach'],
        'peConfidence' => $definition['confidence'],
        'peEvidenceCoverage' => $definition['coverage'],
        'peQualificationStatus' => 'OUTREACH_READY',
        'pePriorityLevel' => $definition['score'] !== null && $definition['score'] >= 80 ? 'HIGH' : 'NORMAL',
        'peSyncStatus' => $definition['sync'],
        'peLastSyncAt' => $now,
        'peLastResearchedAt' => $definition['research'] === 'COMPLETED' ? $now : null,
        'peProposalEligibility' => $definition['proposalEligible'],
        'peProposalAction' => $definition['proposalAction'],
        'peProposalSuggestedNextAction' => $definition['proposalEligible'] ? 'Synthetic manual proposal review only.' : null,
        'assignedUserId' => $salesUser->getId(),
        'teamsIds' => [$salesTeam->getId()],
    ]);
    $entityManager->saveEntity($lead);
    $lead->set('outreachStatus', $definition['outreach']);
    $entityManager->saveEntity($lead);
    $leads[$key] = $lead;

    if ($definition['evidence'] !== null) {
        $evidence = $entityManager->getEntity('ResearchEvidence');
        $evidence->set([
            'name' => "{$name} Evidence",
            'leadId' => $lead->getId(),
            'peEvidenceId' => "phase3b07-{$key}-evidence",
            'peClaim' => $definition['evidence'],
            'peClaimType' => 'synthetic_validation',
            'peEvidenceType' => 'synthetic_validation',
            'peSourceUrl' => 'https://phase3b07-test.example/evidence',
            'peEvidenceText' => $definition['evidence'],
            'peContentSummary' => $definition['evidence'],
            'peConfidence' => $definition['confidence'] ?? 0.8,
            'peCapturedAt' => $now,
            'peSchemaVersion' => 'phase3b07-test',
            'peSnapshotHash' => str_repeat('7', 64),
            'assignedUserId' => $salesUser->getId(),
        ]);
        $entityManager->saveEntity($evidence);
    }

    echo "PHASE3B07_LEAD_READY {$key} {$lead->getId()}\n";
}

$feedback = $entityManager->getEntity('SalesFeedback');
$feedback->set([
    'name' => "{$marker} Positive Feedback",
    'externalFeedbackId' => 'phase3b07-positive-feedback',
    'externalLeadId' => 'phase3b07-a-tier',
    'feedbackType' => 'INTERESTED',
    'outcome' => 'POSITIVE',
    'reason' => 'Synthetic validation response.',
    'note' => 'Synthetic feedback for operations visibility.',
    'currentStage' => 'QUALIFIED',
    'product' => 'Resin Tank',
    'source' => 'CRM_MANUAL',
    'feedbackAt' => $now,
    'leadId' => $leads['a-tier']->getId(),
    'assignedUserId' => $salesUser->getId(),
]);
$entityManager->saveEntity($feedback);

echo "PHASE3B07_SYNTHETIC_RECORDS_READY\n";
