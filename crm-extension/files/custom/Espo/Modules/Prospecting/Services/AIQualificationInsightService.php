<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates immutable advisory insight records from existing evidence references.
 *
 * This service validates C20 provenance by reference. It does not execute AI,
 * resolve providers, calculate scores, qualify a prospect, or mutate CRM state.
 */
final class AIQualificationInsightService
{
    public const ENTITY_TYPE = 'AIQualificationInsight';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'prospectPoolId',
        'insightContent',
        'signals',
        'reasoning',
        'confidence',
        'evidenceReferences',
        'sourceAIRequestLogId',
        'sourceAIJobId',
        'supersedesId',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
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
                'AIQualificationInsight create contains unsupported fields.'
            );
        }

        $prospectPool = $this->existingEntity(
            'ProspectPool',
            $this->requiredId($attributes, 'prospectPoolId')
        );
        $requestLog = $this->existingEntity(
            'AIRequestLog',
            $this->requiredId($attributes, 'sourceAIRequestLogId')
        );
        $sourceAIJobId = $this->optionalId(
            $attributes['sourceAIJobId'] ?? null
        );
        if (
            $sourceAIJobId !== null
            && (string) $requestLog->get('aiJobId') !== $sourceAIJobId
        ) {
            throw new BadRequest(
                'AIQualificationInsight sourceAIJobId must match sourceAIRequestLogId.'
            );
        }

        $evidenceList = $this->evidenceReferences(
            $attributes['evidenceReferences'] ?? null,
            (string) $prospectPool->getId()
        );
        $supersedesId = $this->optionalId(
            $attributes['supersedesId'] ?? null
        );
        if ($supersedesId !== null) {
            $this->assertSupersession(
                $supersedesId,
                (string) $prospectPool->getId()
            );
        }

        $signals = $this->signals($attributes['signals'] ?? null);
        $insight = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $insight->set([
            'name' => 'Advisory Insight: ' . $prospectPool->getId(),
            'prospectPoolId' => $prospectPool->getId(),
            'insightContent' => $this->requiredText(
                $attributes,
                'insightContent'
            ),
            'signals' => json_encode(
                $signals,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'reasoning' => $this->requiredText($attributes, 'reasoning'),
            'confidence' => $this->confidence(
                $attributes['confidence'] ?? null
            ),
            'evidenceReferenceIds' => json_encode(
                array_map(
                    static fn (Entity $evidence): string =>
                        (string) $evidence->getId(),
                    $evidenceList
                ),
                JSON_THROW_ON_ERROR
            ),
            'sourceAIRequestLogId' => $requestLog->getId(),
            'sourceAIJobId' => $sourceAIJobId,
            'supersedesId' => $supersedesId,
        ]);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($insight, $evidenceList): Entity {
                $this->entityManager->saveEntity($insight, [
                    C21IntelligenceSaveOption::INSIGHT_CREATE_AUTHORIZED => true,
                ]);

                $relation = $this->entityManager
                    ->getRDBRepository(self::ENTITY_TYPE)
                    ->getRelation($insight, 'evidenceReferences');
                foreach ($evidenceList as $evidence) {
                    $relation->relate($evidence);
                }

                return $insight;
            }
        );
    }

    /**
     * @return list<Entity>
     */
    private function evidenceReferences(
        mixed $value,
        string $prospectPoolId
    ): array {
        if (!is_array($value) || $value === [] || count($value) > 100) {
            throw new BadRequest(
                'AIQualificationInsight requires 1 to 100 evidence references.'
            );
        }

        $ids = [];
        $evidenceList = [];
        foreach ($value as $id) {
            $id = $this->optionalId($id);
            if ($id === null || in_array($id, $ids, true)) {
                throw new BadRequest(
                    'AIQualificationInsight evidence references must be unique IDs.'
                );
            }
            $evidence = $this->existingEntity('ResearchEvidence', $id);
            if ((string) $evidence->get('prospectPoolId') !== $prospectPoolId) {
                throw new BadRequest(
                    'AIQualificationInsight evidence must belong to its ProspectPool.'
                );
            }
            $ids[] = $id;
            $evidenceList[] = $evidence;
        }

        return $evidenceList;
    }

    private function assertSupersession(
        string $predecessorId,
        string $prospectPoolId
    ): void {
        $predecessor = $this->existingEntity(
            self::ENTITY_TYPE,
            $predecessorId
        );
        if ((string) $predecessor->get('prospectPoolId') !== $prospectPoolId) {
            throw new BadRequest(
                'A superseding insight must retain the same ProspectPool.'
            );
        }

        $successor = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['supersedesId' => $predecessorId])
            ->findOne();
        if ($successor) {
            throw new Conflict(
                'AIQualificationInsight already has a direct successor.'
            );
        }
    }

    private function existingEntity(string $entityType, string $id): Entity
    {
        $entity = $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            throw new BadRequest(
                "AIQualificationInsight requires existing {$entityType}."
            );
        }
        if (!$this->acl->checkEntityRead($entity)) {
            throw new Forbidden();
        }

        return $entity;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function requiredId(array $attributes, string $field): string
    {
        $value = $this->optionalId($attributes[$field] ?? null);
        if ($value === null) {
            throw new BadRequest(
                "AIQualificationInsight requires {$field}."
            );
        }

        return $value;
    }

    private function optionalId(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function requiredText(array $attributes, string $field): string
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest(
                "AIQualificationInsight requires {$field}."
            );
        }

        return trim($value);
    }

    /**
     * @return list<string>
     */
    private function signals(mixed $value): array
    {
        if (!is_array($value) || $value === [] || count($value) > 100) {
            throw new BadRequest(
                'AIQualificationInsight signals must be a non-empty string list.'
            );
        }

        $signals = [];
        foreach ($value as $signal) {
            if (!is_string($signal) || trim($signal) === '') {
                throw new BadRequest(
                    'AIQualificationInsight signals must be non-empty strings.'
                );
            }
            $signals[] = trim($signal);
        }

        return $signals;
    }

    private function confidence(mixed $value): float
    {
        if (
            (!is_int($value) && !is_float($value))
            || $value < 0
            || $value > 1
        ) {
            throw new BadRequest(
                'AIQualificationInsight confidence must be between 0 and 1.'
            );
        }

        return (float) $value;
    }
}
