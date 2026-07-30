<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Read-only C23 assistant for explaining analytical artifacts to humans.
 *
 * It exposes only summaries and explanations. It has no authority to alter
 * analytical records or initiate an operational change.
 */
final class OptimizationAssistantService
{
    /** @var list<string> */
    private const INPUT_ENTITY_TYPES = [
        'OptimizationInsight',
        'PerformanceMetric',
        'FeedbackLearningObservation',
    ];

    private const DEFAULT_LIMIT = 10;
    private const MAX_LIMIT = 100;

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {
    }

    /**
     * @return array<string, mixed>
     */
    public function summarize(int $limit = self::DEFAULT_LIMIT): array
    {
        $limit = $this->validatedLimit($limit);

        return [
            'summary' =>
                'C23 analytical artifacts are available for human review only. '
                . 'No operational action follows from this summary.',
            'recentInsights' => $this->recentSummaries(
                'OptimizationInsight',
                $limit
            ),
            'metricSummaries' => $this->recentSummaries(
                'PerformanceMetric',
                $limit
            ),
            'learningObservations' => $this->recentSummaries(
                'FeedbackLearningObservation',
                $limit
            ),
        ];
    }

    /**
     * @return array<string, mixed>
     */
    public function explain(string $entityType, string $id): array
    {
        $entity = $this->read($entityType, $id);

        return [
            'entityType' => $entity->getEntityType(),
            'id' => $entity->getId(),
            'explanation' => $this->explanation($entity),
            'record' => $this->recordSummary($entity),
        ];
    }

    public function read(string $entityType, string $id): Entity
    {
        $this->assertInputEntityType($entityType);
        $id = trim($id);
        $entity = $id === ''
            ? null
            : $this->entityManager->getEntity($entityType, $id);
        if (!$entity || $entity->isNew()) {
            throw new BadRequest("{$entityType} does not exist.");
        }
        if (!$this->acl->checkEntityRead($entity)) {
            throw new Forbidden();
        }

        return $entity;
    }

    /** @return list<array<string, mixed>> */
    private function recentSummaries(string $entityType, int $limit): array
    {
        $this->assertInputEntityType($entityType);
        $summaries = [];
        foreach (
            $this->entityManager
                ->getRDBRepository($entityType)
                ->order('createdAt', 'desc')
                ->find() as $entity
        ) {
            if (!$this->acl->checkEntityRead($entity)) {
                continue;
            }
            $summaries[] = $this->recordSummary($entity);
            if (count($summaries) === $limit) {
                break;
            }
        }

        return $summaries;
    }

    /** @return array<string, mixed> */
    private function recordSummary(Entity $entity): array
    {
        $summary = [
            'entityType' => $entity->getEntityType(),
            'id' => $entity->getId(),
        ];
        foreach (['status', 'freshnessStatus', 'generatedAt', 'createdAt'] as $field) {
            $value = $entity->get($field);
            if ($value !== null && $value !== '') {
                $summary[$field] = $value;
            }
        }

        return $summary;
    }

    private function explanation(Entity $entity): string
    {
        return match ($entity->getEntityType()) {
            'OptimizationInsight' =>
                'This is an advisory optimization insight for human review. '
                . 'Its lifecycle status does not authorize an operational change.',
            'PerformanceMetric' =>
                'This is an aggregate measurement artifact for human interpretation.',
            'FeedbackLearningObservation' =>
                'This is an aggregate feedback-learning observation for human consideration.',
            default => throw new BadRequest('Unsupported assistant record.'),
        };
    }

    private function assertInputEntityType(string $entityType): void
    {
        if (!in_array($entityType, self::INPUT_ENTITY_TYPES, true)) {
            throw new BadRequest('Unsupported assistant input entity type.');
        }
    }

    private function validatedLimit(int $limit): int
    {
        if ($limit < 1 || $limit > self::MAX_LIMIT) {
            throw new BadRequest(
                'OptimizationAssistantService limit must be between 1 and 100.'
            );
        }

        return $limit;
    }
}
