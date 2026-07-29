<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Appends human review signals without mutating their intelligence target.
 */
final class HumanFeedbackService
{
    public const ENTITY_TYPE = 'HumanFeedback';

    /** @var list<string> */
    private const TARGET_TYPES = [
        'AIQualificationInsight',
        'ResearchEvidence',
        'ProspectPool',
    ];

    /** @var list<string> */
    private const FEEDBACK_TYPES = [
        'CONFIRM',
        'CORRECT',
        'DISAGREE',
        'COMMENT',
    ];

    /** @var list<string> */
    private const ASSESSMENTS = [
        'SUPPORTS',
        'PARTIALLY_SUPPORTS',
        'DOES_NOT_SUPPORT',
        'NOT_APPLICABLE',
    ];

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'targetType',
        'targetId',
        'feedbackType',
        'comment',
        'assessment',
        'supersedesId',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {
    }

    /**
     * @param array<string, mixed> $attributes
     */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest(
                'HumanFeedback create contains unsupported fields.'
            );
        }

        $targetType = $this->requiredEnum(
            $attributes,
            'targetType',
            self::TARGET_TYPES
        );
        $targetId = $this->requiredString($attributes, 'targetId');
        $target = $this->entityManager->getEntity($targetType, $targetId);
        if (!$target || $target->isNew()) {
            throw new BadRequest(
                'HumanFeedback target must reference existing C21 intelligence.'
            );
        }
        if (!$this->acl->checkEntityRead($target)) {
            throw new Forbidden();
        }

        $feedbackType = $this->requiredEnum(
            $attributes,
            'feedbackType',
            self::FEEDBACK_TYPES
        );
        $comment = $this->optionalString($attributes['comment'] ?? null);
        if (
            in_array($feedbackType, ['CORRECT', 'COMMENT'], true)
            && $comment === null
        ) {
            throw new BadRequest(
                "HumanFeedback {$feedbackType} requires comment."
            );
        }
        $assessment = $this->optionalEnum(
            $attributes['assessment'] ?? null,
            self::ASSESSMENTS
        );
        $supersedesId = $this->optionalString(
            $attributes['supersedesId'] ?? null
        );
        if ($supersedesId !== null) {
            $this->assertSupersession(
                $supersedesId,
                $targetType,
                $targetId
            );
        }

        $actorId = $this->optionalString($this->user->getId());
        if ($actorId === null) {
            throw new BadRequest('HumanFeedback requires an authenticated actor.');
        }

        $feedback = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $feedback->set([
            'name' => 'Human Feedback: ' . $feedbackType,
            'targetType' => $targetType,
            'targetId' => $targetId,
            'feedbackType' => $feedbackType,
            'comment' => $comment,
            'assessment' => $assessment,
            'actorId' => $actorId,
            'supersedesId' => $supersedesId,
        ]);
        $this->entityManager->saveEntity($feedback, [
            C21IntelligenceSaveOption::HUMAN_FEEDBACK_CREATE_AUTHORIZED => true,
        ]);

        return $feedback;
    }

    private function assertSupersession(
        string $predecessorId,
        string $targetType,
        string $targetId
    ): void {
        $predecessor = $this->entityManager->getEntity(
            self::ENTITY_TYPE,
            $predecessorId
        );
        if (!$predecessor || $predecessor->isNew()) {
            throw new BadRequest(
                'HumanFeedback supersedesId must reference existing feedback.'
            );
        }
        if (!$this->acl->checkEntityRead($predecessor)) {
            throw new Forbidden();
        }
        if (
            (string) $predecessor->get('targetType') !== $targetType
            || (string) $predecessor->get('targetId') !== $targetId
        ) {
            throw new BadRequest(
                'Superseding HumanFeedback must retain the same target.'
            );
        }

        $successor = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['supersedesId' => $predecessorId])
            ->findOne();
        if ($successor) {
            throw new Conflict(
                'HumanFeedback already has a direct successor.'
            );
        }
    }

    /**
     * @param array<string, mixed> $attributes
     * @param list<string> $allowed
     */
    private function requiredEnum(
        array $attributes,
        string $field,
        array $allowed
    ): string {
        $value = $this->requiredString($attributes, $field);
        if (!in_array($value, $allowed, true)) {
            throw new BadRequest("HumanFeedback has invalid {$field}.");
        }

        return $value;
    }

    /**
     * @param list<string> $allowed
     */
    private function optionalEnum(mixed $value, array $allowed): ?string
    {
        $value = $this->optionalString($value);
        if ($value !== null && !in_array($value, $allowed, true)) {
            throw new BadRequest('HumanFeedback has invalid assessment.');
        }

        return $value;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function requiredString(array $attributes, string $field): string
    {
        $value = $this->optionalString($attributes[$field] ?? null);
        if ($value === null) {
            throw new BadRequest("HumanFeedback requires {$field}.");
        }

        return $value;
    }

    private function optionalString(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
