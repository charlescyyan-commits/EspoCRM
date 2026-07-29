<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Hooks\ResearchEvidence;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeRemove;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\ResearchEvidenceSaveOption;
use Espo\Modules\Prospecting\Services\ResearchEvidenceService;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use Espo\ORM\Repository\Option\RemoveOptions;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for C21 immutable intelligence evidence.
 */
final class ResearchEvidenceGovernanceGuard implements BeforeSave, BeforeRemove
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_CORE_FIELDS = [
        'peEvidenceId',
        'peClaim',
        'peClaimType',
        'peEvidenceType',
        'peEvidenceTypeNormalized',
        'peEvidenceText',
        'peContentSummary',
        'peSourceUrl',
        'peCanonicalUrl',
        'peCapturedAt',
        'peSchemaVersion',
        'peSnapshotHash',
        'peClaimHash',
        'peConfidence',
        'provenanceReference',
        'sourceAIRequestLogId',
        'sourceAIJobId',
        'supersedesId',
    ];

    public function __construct(private EntityManager $entityManager)
    {
    }

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            $this->prepareAndValidateCreate($entity, $options);

            return;
        }

        $this->assertImmutableCoreUnchanged($entity);
        $this->assertLegacyClassificationMutation($entity, $options);
        $this->assertValidationMutation($entity, $options);
        $this->assertParentMutation($entity, $options);
    }

    public function beforeRemove(Entity $entity, RemoveOptions $options): void
    {
        throw new Forbidden(
            'ResearchEvidence history is immutable and cannot be deleted.'
        );
    }

    private function prepareAndValidateCreate(
        Entity $entity,
        SaveOptions $options
    ): void {
        $reason = (string) ($entity->get('classificationReason') ?: '');
        $correctionAuthorized = $options->get(
            ResearchEvidenceSaveOption::CORRECTION_CREATE_AUTHORIZED
        ) === true;

        if ($reason === ResearchEvidenceService::CLASSIFICATION_EXPLICIT_CORRECTION) {
            if (!$correctionAuthorized || !$entity->get('supersedesId')) {
                throw new Forbidden(
                    'ResearchEvidence correction creation must use the governance service.'
                );
            }
        } else {
            ResearchEvidenceService::prepareExplicitCreate($entity);
        }

        ResearchEvidenceService::assertCreateContract($entity);
        $this->assertProvenanceConsistency($entity);
        $this->assertSupersessionTarget($entity);
    }

    private function assertImmutableCoreUnchanged(Entity $entity): void
    {
        foreach (self::IMMUTABLE_CORE_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "ResearchEvidence immutable field {$field} cannot be modified; create a correction record."
                );
            }
        }
    }

    private function assertLegacyClassificationMutation(
        Entity $entity,
        SaveOptions $options
    ): void {
        if (
            !$entity->isAttributeChanged('evidenceType')
            && !$entity->isAttributeChanged('classificationReason')
        ) {
            return;
        }

        $authorized = $options->get(
            ResearchEvidenceSaveOption::LEGACY_CLASSIFICATION_AUTHORIZED
        ) === true;
        $fromType = (string) $entity->getFetched('evidenceType');
        $toType = (string) $entity->get('evidenceType');
        $fromReason = (string) $entity->getFetched('classificationReason');
        $toReason = (string) $entity->get('classificationReason');

        if (
            !$authorized
            || $fromType !== ResearchEvidenceService::TYPE_UNKNOWN
            || !in_array(
                $toType,
                ResearchEvidenceService::GOVERNED_EVIDENCE_TYPES,
                true
            )
            || $fromReason !== ResearchEvidenceService::CLASSIFICATION_LEGACY_UNCLASSIFIED
            || $toReason !== ResearchEvidenceService::CLASSIFICATION_LEGACY_MANUAL_REVIEW
        ) {
            throw new Forbidden(
                'ResearchEvidence classification is immutable except for one reviewed legacy classification.'
            );
        }

        ResearchEvidenceService::assertCreateContract($entity, true);
        $this->assertProvenanceConsistency($entity);
    }

    private function assertValidationMutation(
        Entity $entity,
        SaveOptions $options
    ): void {
        if (!$entity->isAttributeChanged('validationState')) {
            return;
        }

        if (
            $options->get(
                ResearchEvidenceSaveOption::VALIDATION_MUTATION_AUTHORIZED
            ) !== true
        ) {
            throw new Forbidden(
                'ResearchEvidence validationState mutation must use the governance service.'
            );
        }

        $from = (string) $entity->getFetched('validationState');
        $to = (string) $entity->get('validationState');
        $allowed = [
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

        if (!in_array($to, $allowed[$from] ?? [], true)) {
            throw new BadRequest(
                "ResearchEvidence validation transition {$from} -> {$to} is not allowed."
            );
        }
    }

    private function assertParentMutation(
        Entity $entity,
        SaveOptions $options
    ): void {
        if ($entity->isAttributeChanged('prospectPoolId')) {
            throw new Forbidden(
                'ResearchEvidence prospectPoolId is immutable.'
            );
        }
        if (!$entity->isAttributeChanged('leadId')) {
            return;
        }

        $authorized = $options->get(
            ResearchEvidenceSaveOption::LEAD_ATTACHMENT_AUTHORIZED
        ) === true;
        if (
            !$authorized
            || $entity->getFetched('leadId')
            || !$entity->get('leadId')
            || !$entity->get('prospectPoolId')
        ) {
            throw new Forbidden(
                'ResearchEvidence Lead attachment must use the frozen promotion inheritance service.'
            );
        }
    }

    private function assertProvenanceConsistency(Entity $entity): void
    {
        $requestLogId = trim((string) $entity->get('sourceAIRequestLogId'));
        $jobId = trim((string) $entity->get('sourceAIJobId'));

        if ($requestLogId === '') {
            return;
        }

        $requestLog = $this->entityManager->getEntity(
            'AIRequestLog',
            $requestLogId
        );
        if (!$requestLog || $requestLog->isNew()) {
            throw new BadRequest(
                'sourceAIRequestLogId must reference an existing AIRequestLog.'
            );
        }

        if (
            $jobId !== ''
            && (string) $requestLog->get('aiJobId') !== $jobId
        ) {
            throw new BadRequest(
                'sourceAIJobId must match the AIJob owned by sourceAIRequestLogId.'
            );
        }
    }

    private function assertSupersessionTarget(Entity $entity): void
    {
        $supersedesId = trim((string) $entity->get('supersedesId'));
        if ($supersedesId === '') {
            return;
        }
        if ($supersedesId === (string) $entity->getId()) {
            throw new BadRequest(
                'ResearchEvidence cannot supersede itself.'
            );
        }

        $predecessor = $this->entityManager->getEntity(
            'ResearchEvidence',
            $supersedesId
        );
        if (!$predecessor || $predecessor->isNew()) {
            throw new BadRequest(
                'supersedesId must reference existing ResearchEvidence.'
            );
        }
        if (
            (string) $predecessor->get('validationState')
            === ResearchEvidenceService::VALIDATION_SUPERSEDED
        ) {
            throw new BadRequest(
                'ResearchEvidence cannot supersede an already superseded record.'
            );
        }
    }
}
