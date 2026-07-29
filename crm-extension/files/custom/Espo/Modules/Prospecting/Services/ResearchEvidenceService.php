<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Record\Service;
use Espo\ORM\Entity;

/**
 * ResearchEvidence entity service.
 *
 * Enforces local create/update invariants for the existing record controller.
 * Cross-record provenance and persistence-path protection are enforced by the
 * ResearchEvidence governance hook.
 */
class ResearchEvidenceService extends Service
{
    public const TYPE_UNKNOWN = 'UNKNOWN';
    public const TYPE_FACT = 'FACT';
    public const TYPE_OBSERVATION = 'OBSERVATION';
    public const TYPE_AI_INFERENCE = 'AI_INFERENCE';

    public const CLASSIFICATION_LEGACY_UNCLASSIFIED = 'LEGACY_UNCLASSIFIED';
    public const CLASSIFICATION_LEGACY_MANUAL_REVIEW = 'LEGACY_MANUAL_REVIEW';
    public const CLASSIFICATION_EXPLICIT_CREATE = 'EXPLICIT_CREATE';
    public const CLASSIFICATION_EXPLICIT_CORRECTION = 'EXPLICIT_CORRECTION';

    public const VALIDATION_UNVALIDATED = 'UNVALIDATED';
    public const VALIDATION_VERIFIED = 'VERIFIED';
    public const VALIDATION_REJECTED = 'REJECTED';
    public const VALIDATION_SUPERSEDED = 'SUPERSEDED';

    /** @var list<string> */
    public const GOVERNED_EVIDENCE_TYPES = [
        self::TYPE_FACT,
        self::TYPE_OBSERVATION,
        self::TYPE_AI_INFERENCE,
    ];

    /** @var list<string> */
    public const VALIDATION_STATES = [
        self::VALIDATION_UNVALIDATED,
        self::VALIDATION_VERIFIED,
        self::VALIDATION_REJECTED,
        self::VALIDATION_SUPERSEDED,
    ];

    /**
     * Validate a controller create without deriving governance from confidence.
     */
    protected function beforeCreate(Entity $entity, $data): void
    {
        parent::beforeCreate($entity, $data);
        self::prepareExplicitCreate($entity);
        self::assertCreateContract($entity);
    }

    /**
     * Validate that the entity retains at least one parent on update.
     */
    protected function beforeUpdate(Entity $entity, $data): void
    {
        parent::beforeUpdate($entity, $data);
        self::validateParentLink($entity);
    }

    public static function prepareExplicitCreate(Entity $entity): void
    {
        $reason = (string) ($entity->get('classificationReason') ?: '');
        if (
            $reason === ''
            || $reason === self::CLASSIFICATION_LEGACY_UNCLASSIFIED
        ) {
            $entity->set(
                'classificationReason',
                self::CLASSIFICATION_EXPLICIT_CREATE
            );
        }
        if (!$entity->get('validationState')) {
            $entity->set('validationState', self::VALIDATION_UNVALIDATED);
        }
    }

    /**
     * Validate all local facts required for a newly persisted evidence record.
     */
    public static function assertCreateContract(
        Entity $entity,
        bool $allowReviewedLegacy = false
    ): void
    {
        self::validateParentLink($entity);

        $evidenceType = (string) ($entity->get('evidenceType') ?: '');
        if (!in_array($evidenceType, self::GOVERNED_EVIDENCE_TYPES, true)) {
            throw new BadRequest(
                'New ResearchEvidence requires an explicit FACT, OBSERVATION, or AI_INFERENCE classification.'
            );
        }

        $reason = (string) ($entity->get('classificationReason') ?: '');
        $allowedReasons = [
            self::CLASSIFICATION_EXPLICIT_CREATE,
            self::CLASSIFICATION_EXPLICIT_CORRECTION,
        ];
        if ($allowReviewedLegacy) {
            $allowedReasons[] = self::CLASSIFICATION_LEGACY_MANUAL_REVIEW;
        }
        if (!in_array($reason, $allowedReasons, true)) {
            throw new BadRequest(
                'New ResearchEvidence requires an explicit classification reason.'
            );
        }

        if (
            (string) ($entity->get('validationState') ?: self::VALIDATION_UNVALIDATED)
            !== self::VALIDATION_UNVALIDATED
        ) {
            throw new BadRequest(
                'New ResearchEvidence must start UNVALIDATED.'
            );
        }

        $provenanceReference = self::optionalString(
            $entity->get('provenanceReference')
        );
        if (
            $provenanceReference === null
            || (
                in_array($reason, [
                    self::CLASSIFICATION_EXPLICIT_CREATE,
                    self::CLASSIFICATION_EXPLICIT_CORRECTION,
                ], true)
                && $provenanceReference === self::CLASSIFICATION_LEGACY_UNCLASSIFIED
            )
        ) {
            throw new BadRequest(
                'New ResearchEvidence requires provenanceReference.'
            );
        }

        $sourceAIRequestLogId = self::optionalString(
            $entity->get('sourceAIRequestLogId')
        );
        $sourceAIJobId = self::optionalString($entity->get('sourceAIJobId'));

        if (
            $evidenceType === self::TYPE_AI_INFERENCE
            && $sourceAIRequestLogId === null
        ) {
            throw new BadRequest(
                'AI_INFERENCE ResearchEvidence requires sourceAIRequestLogId.'
            );
        }
        if ($sourceAIJobId !== null && $sourceAIRequestLogId === null) {
            throw new BadRequest(
                'sourceAIJobId cannot be stored without sourceAIRequestLogId.'
            );
        }

        if (
            in_array($evidenceType, [self::TYPE_FACT, self::TYPE_OBSERVATION], true)
            && $sourceAIRequestLogId === null
            && self::optionalString($entity->get('peSourceUrl')) === null
            && self::optionalString($entity->get('peCanonicalUrl')) === null
        ) {
            throw new BadRequest(
                'FACT or OBSERVATION ResearchEvidence requires an attributable source.'
            );
        }
    }

    /**
     * Assert that ResearchEvidence has at least one parent reference.
     *
     * Evidence must be linked to a Lead, a ProspectPool, or both.
     * Evidence with neither parent is rejected.
     *
     * @throws BadRequest when both leadId and prospectPoolId are empty.
     */
    public static function validateParentLink(Entity $entity): void
    {
        $leadId = $entity->get('leadId');
        $prospectPoolId = $entity->get('prospectPoolId');

        if (empty($leadId) && empty($prospectPoolId)) {
            throw new BadRequest(
                'ResearchEvidence must be linked to a Lead or a ProspectPool.'
            );
        }
    }

    private static function optionalString(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }

        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
