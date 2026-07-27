<?php

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\ORM\EntityManager;
use Psr\Log\LoggerInterface;

/**
 * Handles evidence inheritance when a ProspectPool is promoted to a Lead.
 *
 * Frozen decision: Evidence inheritance must be idempotent.
 * - Preserve the prospectPool relation.
 * - Attach the lead relation.
 * - Never duplicate evidence rows.
 */
class PromotionInheritanceService
{
    private const ENTITY_TYPE = 'ResearchEvidence';

    public function __construct(
        private EntityManager $entityManager,
        private LoggerInterface $log,
    ) {}

    /**
     * Link all ResearchEvidence from a ProspectPool to a Lead.
     *
     * Idempotent: evidence already linked to the given lead is skipped.
     * Evidence linked to a different lead throws — each evidence row
     * belongs to at most one lead.
     *
     * @param string $prospectPoolId The source ProspectPool ID.
     * @param string $leadId         The target Lead ID.
     * @return array{linked: int, skipped: int} Counts of linked and skipped evidence rows.
     *
     * @throws BadRequest When either ID is empty.
     * @throws Conflict   When evidence is already linked to a different lead.
     */
    public function inheritEvidenceToLead(string $prospectPoolId, string $leadId): array
    {
        if (empty($prospectPoolId)) {
            throw new BadRequest('ProspectPool ID is required for evidence inheritance.');
        }
        if (empty($leadId)) {
            throw new BadRequest('Lead ID is required for evidence inheritance.');
        }

        $this->log->info(
            "PromotionInheritance: inheriting evidence from ProspectPool {$prospectPoolId} to Lead {$leadId}"
        );

        $evidenceList = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['prospectPoolId' => $prospectPoolId])
            ->find();

        $linked = 0;
        $skipped = 0;

        foreach ($evidenceList as $evidence) {
            $currentLeadId = $evidence->get('leadId');

            // Already linked to the same lead — idempotent skip.
            if ($currentLeadId === $leadId) {
                $skipped++;
                continue;
            }

            // Evidence is already linked to a different lead — reject.
            if (!empty($currentLeadId) && $currentLeadId !== $leadId) {
                throw new Conflict(
                    "ResearchEvidence {$evidence->getId()} is already linked to Lead {$currentLeadId}. " .
                    "Cannot reassign to Lead {$leadId}."
                );
            }

            // Link the evidence to the lead while preserving the prospectPool link.
            $evidence->set('leadId', $leadId);
            $this->entityManager->saveEntity($evidence);
            $linked++;
        }

        $this->log->info(
            "PromotionInheritance: linked {$linked}, skipped {$skipped} evidence rows " .
            "for ProspectPool {$prospectPoolId} → Lead {$leadId}"
        );

        return [
            'linked' => $linked,
            'skipped' => $skipped,
        ];
    }
}
