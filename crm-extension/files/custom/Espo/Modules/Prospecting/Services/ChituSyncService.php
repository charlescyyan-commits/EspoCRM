<?php

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Exceptions\NotFound;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use stdClass;

class ChituSyncService
{
    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    public function syncLead(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->findLead($payload['identity']['candidate_id']);
        $created = $lead === null;

        if ($created) {
            $this->assertScope('Lead', 'create');
            $lead = $this->entityManager->getEntity('Lead');
        } elseif (!$this->acl->checkEntityEdit($lead)) {
            throw new Forbidden();
        }

        $lead->set($this->leadFields($payload));
        $this->entityManager->saveEntity($lead);

        return $this->response($lead, $payload, $created, !$created);
    }

    public function syncEvidence(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->requiredLead($payload['identity']['candidate_id']);

        if (!$this->acl->checkEntityRead($lead)) {
            throw new Forbidden();
        }
        $this->assertScope('ResearchEvidence', 'create');

        $ids = [];
        $lastEvidence = null;
        $createdAny = false;
        $updatedAny = false;
        foreach ($payload['evidence'] as $item) {
            $identity = $this->evidenceIdentity($lead->getId(), $item);
            $evidence = $this->findEvidenceByIdentity(
                $lead->getId(),
                $identity['canonicalUrl'],
                $identity['normalizedEvidenceType'],
                $identity['claimHash'],
            );
            if ($evidence === null) {
                $evidence = $this->entityManager->getEntity('ResearchEvidence');
                $createdAny = true;
            } elseif (!$this->acl->checkEntityEdit($evidence)) {
                throw new Forbidden();
            } else {
                $updatedAny = true;
            }
            $evidence->set([
                'name' => $payload['company']['name'] . ' — ' . $item['evidence_id'],
                'leadId' => $lead->getId(),
                'peEvidenceId' => $item['evidence_id'],
                'peClaim' => $item['claim'],
                'peClaimType' => $item['claim_type'],
                'peEvidenceType' => $this->evidenceType($item),
                'peSourceUrl' => $item['source_url'],
                'peEvidenceText' => $item['evidence_text'],
                'peContentSummary' => $item['evidence_text'],
                'peConfidence' => $item['confidence'],
                'peCapturedAt' => $this->dateTime($item['captured_at']),
                'peSchemaVersion' => $item['schema_version'],
                'peSnapshotHash' => $payload['provenance']['evidence_snapshot_hash'],
                'peCanonicalUrl' => $identity['canonicalUrl'],
                'peEvidenceTypeNormalized' => $identity['normalizedEvidenceType'],
                'peClaimHash' => $identity['claimHash'],
            ]);
            $this->entityManager->saveEntity($evidence);
            $ids[] = $evidence->getId();
            $lastEvidence = $evidence;
        }

        $result = $this->response($lastEvidence, $payload, $createdAny, $updatedAny);
        $result['crm_ids'] = $ids;
        $result['evidence_count'] = count($ids);

        return $result;
    }

    /**
     * Find a currently active row by the C10.6 identity columns. The database
     * unique index remains the final guard against concurrent inserts.
     */
    private function findEvidenceByIdentity(
        string $leadId,
        string $canonicalUrl,
        string $normalizedEvidenceType,
        string $claimHash,
    ): ?Entity {
        return $this->entityManager->getRDBRepository('ResearchEvidence')
            ->where([
                'leadId' => $leadId,
                'peCanonicalUrl' => $canonicalUrl,
                'peEvidenceTypeNormalized' => $normalizedEvidenceType,
                'peClaimHash' => $claimHash,
            ])
            ->findOne();
    }

    /**
     * @return array{canonicalUrl: string, normalizedEvidenceType: string, claimHash: string}
     */
    private function evidenceIdentity(string $leadId, array $item): array
    {
        if ($leadId === '') {
            throw new BadRequest('Missing evidence lead ID.');
        }
        $canonicalUrl = $this->canonicalUrl($this->evidenceString($item, 'source_url'));
        $normalizedEvidenceType = $this->normalizeEvidenceType($this->evidenceType($item));
        $claimHash = hash('sha256', $this->normalizeText($this->evidenceString($item, 'claim')));

        return [
            'canonicalUrl' => $canonicalUrl,
            'normalizedEvidenceType' => $normalizedEvidenceType,
            'claimHash' => $claimHash,
        ];
    }

    /**
     * `evidence_type` is an optional, backward-compatible V1 pass-through.
     * Legacy payloads receive an explicit unknown value; claim_type is never
     * used as the evidence-format classification.
     */
    private function evidenceType(array $item): string
    {
        $value = $item['evidence_type'] ?? null;

        return is_string($value) && trim($value) !== '' ? trim($value) : 'LEGACY_UNKNOWN';
    }

    private function evidenceString(array $item, string $name): string
    {
        $value = $item[$name] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("Missing evidence field: {$name}.");
        }

        return trim($value);
    }

    private function canonicalUrl(string $value): string
    {
        $parts = parse_url($value);
        if ($parts === false || !isset($parts['scheme'], $parts['host'])) {
            throw new BadRequest('Invalid evidence source URL.');
        }
        $scheme = strtolower($parts['scheme']);
        $host = strtolower($parts['host']);
        if (!in_array($scheme, ['http', 'https'], true) || $host === '') {
            throw new BadRequest('Invalid evidence source URL.');
        }
        $port = $parts['port'] ?? null;
        $portPart = $port !== null && !(($scheme === 'http' && $port === 80) || ($scheme === 'https' && $port === 443))
            ? ':' . $port
            : '';
        $path = $parts['path'] ?? '/';
        $path = $path === '/' ? '/' : rtrim($path, '/');
        $query = $this->canonicalQuery($parts['query'] ?? '');
        $canonical = $scheme . '://' . $host . $portPart . $path . ($query === '' ? '' : '?' . $query);
        if (strlen($canonical) > 255) {
            throw new BadRequest('Canonical evidence source URL is too long.');
        }

        return $canonical;
    }

    private function canonicalQuery(string $query): string
    {
        if ($query === '') {
            return '';
        }
        $pairs = [];
        foreach (explode('&', $query) as $part) {
            $pair = explode('=', $part, 2);
            $key = rawurldecode($pair[0]);
            $value = rawurldecode($pair[1] ?? '');
            $pairs[] = rawurlencode($key) . '=' . rawurlencode($value);
        }
        sort($pairs, SORT_STRING);

        return implode('&', $pairs);
    }

    private function normalizeEvidenceType(string $value): string
    {
        $normalized = strtolower($this->normalizeText($value));
        if (strlen($normalized) > 100) {
            throw new BadRequest('Evidence type is too long.');
        }

        return $normalized;
    }

    private function normalizeText(string $value): string
    {
        return preg_replace('/\s+/u', ' ', trim($value)) ?? trim($value);
    }

    public function syncOpportunityProposal(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->requiredLead($payload['identity']['candidate_id']);

        if (!$this->acl->checkEntityEdit($lead)) {
            throw new Forbidden();
        }

        $score = (float) $payload['score']['value'];
        if ($score < 80) {
            return $this->response($lead, $payload, false, false, false);
        }

        $created = $lead->get('peProposalAction') === null;
        $lead->set([
            'peBestFirstProduct' => $payload['recommendation']['best_first_product'],
            'peOpportunityScoreV4' => $score,
            'peProposalProductFitScore' => $score,
            'peProposalCooperationType' => null,
            'peProposalSuggestedNextAction' => 'Human review required before creating a CRM Opportunity.',
            'peProposalEligibility' => true,
            'peProposalAction' => 'NO_AUTOMATIC_OPPORTUNITY',
        ]);
        $this->entityManager->saveEntity($lead);

        return $this->response($lead, $payload, $created, !$created, true);
    }

    private function payload(stdClass $body): array
    {
        $payload = json_decode(json_encode($body, JSON_THROW_ON_ERROR), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($payload) || ($payload['contract_version'] ?? null) !== '1.0') {
            throw new BadRequest('Unsupported sync contract.');
        }
        foreach (['identity', 'company', 'source', 'research', 'score', 'recommendation', 'evidence', 'provenance', 'sync'] as $key) {
            if (!array_key_exists($key, $payload)) {
                throw new BadRequest("Missing contract field: {$key}.");
            }
        }
        if (!is_array($payload['identity']) || !is_string($payload['identity']['candidate_id'] ?? null) || $payload['identity']['candidate_id'] === '') {
            throw new BadRequest('Missing identity.candidate_id.');
        }
        if (!is_array($payload['evidence']) || !$payload['evidence']) {
            throw new BadRequest('Missing evidence.');
        }

        return $payload;
    }

    private function findLead(string $externalId): ?Entity
    {
        $records = $this->entityManager->getRDBRepository('Lead')
            ->where(['peCandidateId' => $externalId])
            ->find();

        if (count($records) > 1) {
            throw new Conflict('Multiple Leads have the same external ID.');
        }

        return $records[0] ?? null;
    }

    private function requiredLead(string $externalId): Entity
    {
        $lead = $this->findLead($externalId);
        if (!$lead) {
            throw new NotFound('Lead external ID was not found.');
        }

        return $lead;
    }

    private function leadFields(array $payload): array
    {
        $score = (float) $payload['score']['value'];

        return [
            'name' => $payload['company']['name'],
            'lastName' => $payload['company']['name'],
            'website' => $payload['company']['website'],
            'addressCountry' => $payload['company']['country_code'],
            'leadSource' => $payload['source']['channel'],
            'peSourceType' => $payload['source']['channel'],
            'peDiscoverySource' => $payload['source']['source_url'],
            'peSourceSystem' => 'Chitu Intelligence',
            'peCandidateId' => $payload['identity']['candidate_id'],
            'peResearchStatus' => $payload['research']['status'] === 'COMPLETE' ? 'COMPLETED' : 'FAILED',
            'peLastResearchedAt' => $this->dateTime($payload['sync']['requested_at']),
            'peOpportunityScoreV4' => $score,
            'peScoreTier' => $payload['score']['score_tier'],
            'peBestFirstProduct' => $payload['recommendation']['best_first_product'],
            'peResearchSummary' => $this->researchSummary($payload),
            'peKeyEvidence' => $this->keyEvidence($payload),
            'peRecommendedApproach' => $this->recommendedApproach($payload),
            'pePriorityLevel' => $score >= 80 ? 'HIGH' : 'NORMAL',
            'peQualificationStatus' => $payload['qualification']['status'] ?? null,
            'peConfidence' => $payload['score']['aggregate_confidence'],
            'peEvidenceCoverage' => $payload['score']['evidence_coverage'],
            'peEngineVersion' => $payload['provenance']['engine_version'],
            'peScoreRulesVersion' => $payload['score']['rules_version'],
            'peLastSyncAt' => $this->dateTime($payload['sync']['requested_at']),
            'peSyncStatus' => 'SYNCED',
        ];
    }

    private function researchSummary(array $payload): string
    {
        $company = $payload['company']['name'];
        $score = (string) $payload['score']['value'];
        $tier = $payload['score']['score_tier'];
        $product = $payload['recommendation']['best_first_product'];
        $coverage = (string) $payload['score']['evidence_coverage'];

        return "Chitu V1 research for {$company}: score {$score} (tier {$tier}), best first product {$product}, evidence coverage {$coverage}.";
    }

    private function keyEvidence(array $payload): ?string
    {
        $lines = [];
        foreach ($payload['evidence'] as $item) {
            $claim = trim((string) ($item['claim'] ?? ''));
            if ($claim === '') {
                continue;
            }
            $claimType = trim((string) ($item['claim_type'] ?? 'evidence'));
            $lines[] = "- [{$claimType}] {$claim}";
        }

        return $lines ? implode("\n", array_slice($lines, 0, 5)) : null;
    }

    private function recommendedApproach(array $payload): ?string
    {
        $product = trim((string) ($payload['recommendation']['best_first_product'] ?? ''));

        if ($product === '') {
            return null;
        }

        return "Open with {$product} relevance based on the supplied research evidence; keep the first ask reply-oriented.";
    }

    private function dateTime(string $value): string
    {
        return (new \DateTimeImmutable($value))->format('Y-m-d H:i:s');
    }

    private function assertScope(string $scope, string $action): void
    {
        if (!$this->acl->check($scope, $action)) {
            throw new Forbidden();
        }
    }

    private function response(Entity $entity, array $payload, bool $created, bool $updated, ?bool $eligible = null): array
    {
        $result = [
            'success' => true,
            'created' => $created,
            'updated' => $updated,
            'external_id' => $payload['identity']['candidate_id'],
            'crm_id' => $entity->getId(),
        ];
        if ($eligible !== null) {
            $result['eligibility'] = $eligible;
            $result['action'] = 'NO_AUTOMATIC_OPPORTUNITY';
        }

        return $result;
    }
}
