<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Explicit C21 governance actions for validation and correction.
 *
 * This service references C20 provenance records but never creates or updates
 * AIJob, AIRequestLog, or PromptTemplate.
 */
final class ResearchEvidenceGovernanceService
{
    /** @var array<string, list<string>> */
    private const VALIDATION_TRANSITIONS = [
        ResearchEvidenceService::VALIDATION_UNVALIDATED => [
            ResearchEvidenceService::VALIDATION_VERIFIED,
            ResearchEvidenceService::VALIDATION_REJECTED,
            ResearchEvidenceService::VALIDATION_SUPERSEDED,
        ],
        ResearchEvidenceService::VALIDATION_VERIFIED => [
            ResearchEvidenceService::VALIDATION_SUPERSEDED,
        ],
        ResearchEvidenceService::VALIDATION_REJECTED => [
            ResearchEvidenceService::VALIDATION_SUPERSEDED,
        ],
        ResearchEvidenceService::VALIDATION_SUPERSEDED => [],
    ];

    /** @var list<string> */
    private const CORRECTION_FIELDS = [
        'name',
        'evidenceType',
        'peEvidenceId',
        'peClaim',
        'peClaimType',
        'peEvidenceType',
        'peSourceUrl',
        'peEvidenceText',
        'peContentSummary',
        'peConfidence',
        'peCapturedAt',
        'peSchemaVersion',
        'peSnapshotHash',
        'peCanonicalUrl',
        'peEvidenceTypeNormalized',
        'peClaimHash',
        'provenanceReference',
        'sourceAIRequestLogId',
        'sourceAIJobId',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {
    }

    public function classifyLegacy(Entity $evidence, string $evidenceType): Entity
    {
        $this->assertEvidence($evidence);
        $this->assertEditAuthorized($evidence);

        if (
            (string) $evidence->get('evidenceType')
            !== ResearchEvidenceService::TYPE_UNKNOWN
            || (string) $evidence->get('classificationReason')
            !== ResearchEvidenceService::CLASSIFICATION_LEGACY_UNCLASSIFIED
        ) {
            throw new BadRequest(
                'Only an unclassified legacy ResearchEvidence can be classified.'
            );
        }
        if (!in_array(
            $evidenceType,
            ResearchEvidenceService::GOVERNED_EVIDENCE_TYPES,
            true
        )) {
            throw new BadRequest('Unsupported ResearchEvidence classification.');
        }

        $evidence->set([
            'evidenceType' => $evidenceType,
            'classificationReason' =>
                ResearchEvidenceService::CLASSIFICATION_LEGACY_MANUAL_REVIEW,
        ]);
        $this->entityManager->saveEntity($evidence, [
            ResearchEvidenceSaveOption::LEGACY_CLASSIFICATION_AUTHORIZED => true,
        ]);

        return $evidence;
    }

    public function transitionValidation(
        Entity $evidence,
        string $targetState
    ): Entity {
        $this->assertEvidence($evidence);
        $this->assertEditAuthorized($evidence);

        $currentState = (string) (
            $evidence->get('validationState')
            ?: ResearchEvidenceService::VALIDATION_UNVALIDATED
        );
        if (!in_array(
            $targetState,
            self::VALIDATION_TRANSITIONS[$currentState] ?? [],
            true
        )) {
            throw new BadRequest(
                "ResearchEvidence validation transition {$currentState} -> {$targetState} is not allowed."
            );
        }

        $evidence->set('validationState', $targetState);
        $this->entityManager->saveEntity($evidence, [
            ResearchEvidenceSaveOption::VALIDATION_MUTATION_AUTHORIZED => true,
        ]);

        return $evidence;
    }

    /**
     * Create a replacement record and preserve the original as SUPERSEDED.
     *
     * @param array<string, mixed> $attributes
     */
    public function createCorrection(
        Entity $original,
        array $attributes
    ): Entity {
        $this->assertEvidence($original);
        $this->assertEditAuthorized($original);
        if (!$this->acl->check('ResearchEvidence', 'create')) {
            throw new Forbidden();
        }
        if (
            (string) $original->get('validationState')
            === ResearchEvidenceService::VALIDATION_SUPERSEDED
        ) {
            throw new BadRequest(
                'A superseded ResearchEvidence cannot be corrected again.'
            );
        }
        if (array_diff(array_keys($attributes), self::CORRECTION_FIELDS) !== []) {
            throw new BadRequest(
                'ResearchEvidence correction contains unsupported fields.'
            );
        }

        $correction = $this->entityManager->getNewEntity('ResearchEvidence');
        foreach (self::CORRECTION_FIELDS as $field) {
            $value = array_key_exists($field, $attributes)
                ? $attributes[$field]
                : $original->get($field);
            $correction->set($field, $value);
        }
        $correction->set([
            'leadId' => $original->get('leadId'),
            'prospectPoolId' => $original->get('prospectPoolId'),
            'assignedUserId' => $original->get('assignedUserId'),
            'classificationReason' =>
                ResearchEvidenceService::CLASSIFICATION_EXPLICIT_CORRECTION,
            'validationState' =>
                ResearchEvidenceService::VALIDATION_UNVALIDATED,
            'supersedesId' => $original->getId(),
            'evidenceRevision' =>
                max(1, (int) $original->get('evidenceRevision')) + 1,
        ]);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($original, $correction): Entity {
                $this->entityManager->saveEntity($correction, [
                    ResearchEvidenceSaveOption::CORRECTION_CREATE_AUTHORIZED => true,
                ]);

                $original->set(
                    'validationState',
                    ResearchEvidenceService::VALIDATION_SUPERSEDED
                );
                $this->entityManager->saveEntity($original, [
                    ResearchEvidenceSaveOption::VALIDATION_MUTATION_AUTHORIZED => true,
                ]);

                return $correction;
            }
        );
    }

    private function assertEvidence(Entity $evidence): void
    {
        if (
            $evidence->getEntityType() !== 'ResearchEvidence'
            || $evidence->isNew()
        ) {
            throw new BadRequest(
                'ResearchEvidence governance requires a persisted ResearchEvidence.'
            );
        }
    }

    private function assertEditAuthorized(Entity $evidence): void
    {
        if (!$this->acl->checkEntityEdit($evidence)) {
            throw new Forbidden();
        }
    }
}
