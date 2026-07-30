<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates and reads immutable, aggregate feedback-learning observations.
 *
 * Source references are stored as provenance data only. This service does not
 * resolve or mutate source records and exposes no operational authority.
 */
final class FeedbackLearningObservationService
{
    public const ENTITY_TYPE = 'FeedbackLearningObservation';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'observationType',
        'description',
        'sourceReference',
        'feedbackReference',
        'metricReference',
        'aggregationPeriodStart',
        'aggregationPeriodEnd',
        'confidence',
        'sampleSize',
        'freshnessStatus',
        'status',
    ];

    /** @var list<string> */
    private const FRESHNESS_STATUSES = [
        'CURRENT',
        'AGING',
        'STALE',
        'ARCHIVAL',
    ];

    /** @var list<string> */
    private const OUTCOME_SOURCE_TYPES = [
        'ProspectRun',
        'ExecutionLedger',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {
    }

    /** @param array<string, mixed> $attributes */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }

        $attributes = $this->validate($attributes);
        $observation = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $observation->set([
            'name' => 'Learning Observation: ' . $attributes['observationType'],
            ...$attributes,
        ]);

        $this->entityManager->saveEntity($observation, [
            C23FeedbackLearningSaveOption::OBSERVATION_CREATE_AUTHORIZED => true,
        ]);

        return $observation;
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $observation = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$observation || $observation->isNew()) {
            throw new BadRequest('FeedbackLearningObservation does not exist.');
        }
        if (!$this->acl->checkEntityRead($observation)) {
            throw new Forbidden();
        }

        return $observation;
    }

    /**
     * @param array<string, mixed> $attributes
     * @return array<string, mixed>
     */
    public function validate(array $attributes): array
    {
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest(
                'FeedbackLearningObservation contains unsupported fields.'
            );
        }

        $start = $this->requiredDate($attributes, 'aggregationPeriodStart');
        $end = $this->requiredDate($attributes, 'aggregationPeriodEnd');
        if ($start > $end) {
            throw new BadRequest(
                'FeedbackLearningObservation aggregation period must be chronological.'
            );
        }

        return [
            'observationType' => $this->requiredText(
                $attributes,
                'observationType'
            ),
            'description' => $this->advisoryDescription(
                $attributes['description'] ?? null
            ),
            'sourceReference' => $this->encodeReferences(
                $attributes['sourceReference'] ?? null,
                self::OUTCOME_SOURCE_TYPES,
                'sourceReference'
            ),
            'feedbackReference' => $this->encodeReferences(
                $attributes['feedbackReference'] ?? null,
                ['HumanFeedback'],
                'feedbackReference'
            ),
            'metricReference' => $this->encodeReferences(
                $attributes['metricReference'] ?? null,
                ['PerformanceMetric'],
                'metricReference'
            ),
            'aggregationPeriodStart' => $start->format('Y-m-d H:i:s'),
            'aggregationPeriodEnd' => $end->format('Y-m-d H:i:s'),
            'confidence' => $this->confidence(
                $attributes['confidence'] ?? null
            ),
            'sampleSize' => $this->sampleSize(
                $attributes['sampleSize'] ?? null
            ),
            'freshnessStatus' => $this->freshnessStatus(
                $attributes['freshnessStatus'] ?? null
            ),
            'status' => $this->initialStatus($attributes['status'] ?? null),
        ];
    }

    /**
     * @param list<string> $allowedEntityTypes
     */
    private function encodeReferences(
        mixed $value,
        array $allowedEntityTypes,
        string $field
    ): string {
        if (!is_array($value) || $value === [] || count($value) > 100) {
            throw new BadRequest(
                "FeedbackLearningObservation {$field} requires 1 to 100 aggregate references."
            );
        }

        $references = [];
        foreach ($value as $reference) {
            if (!is_array($reference)) {
                throw new BadRequest(
                    "FeedbackLearningObservation {$field} must contain reference objects."
                );
            }
            $entityType = $reference['entityType'] ?? null;
            $aggregateKey = $reference['reference'] ?? null;
            if (
                !is_string($entityType)
                || !in_array($entityType, $allowedEntityTypes, true)
                || !is_string($aggregateKey)
                || trim($aggregateKey) === ''
            ) {
                throw new BadRequest(
                    "FeedbackLearningObservation {$field} contains an invalid aggregate reference."
                );
            }
            $references[] = [
                'entityType' => $entityType,
                'reference' => trim($aggregateKey),
            ];
        }

        return json_encode(
            $references,
            JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
        );
    }

    /** @param array<string, mixed> $attributes */
    private function requiredText(array $attributes, string $field): string
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest(
                "FeedbackLearningObservation requires {$field}."
            );
        }

        return trim($value);
    }

    private function advisoryDescription(mixed $value): string
    {
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest(
                'FeedbackLearningObservation requires description.'
            );
        }
        $value = trim($value);
        if (preg_match(
            '/^(approve|send|execute|create|switch|route|schedule|reallocate|trigger|apply)\b/i',
            $value
        ) === 1) {
            throw new BadRequest(
                'FeedbackLearningObservation description must be observational.'
            );
        }

        return $value;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredDate(array $attributes, string $field): DateTimeImmutable
    {
        $value = $attributes[$field] ?? null;
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest(
                "FeedbackLearningObservation requires {$field}."
            );
        }
        try {
            return new DateTimeImmutable($value);
        } catch (\Exception) {
            throw new BadRequest(
                "FeedbackLearningObservation {$field} must be a date."
            );
        }
    }

    private function confidence(mixed $value): float
    {
        if (
            (!is_int($value) && !is_float($value))
            || $value < 0
            || $value > 1
        ) {
            throw new BadRequest(
                'FeedbackLearningObservation confidence must be between 0 and 1.'
            );
        }

        return (float) $value;
    }

    private function sampleSize(mixed $value): int
    {
        if (!is_int($value) || $value < 2) {
            throw new BadRequest(
                'FeedbackLearningObservation sampleSize must be at least 2.'
            );
        }

        return $value;
    }

    private function freshnessStatus(mixed $value): string
    {
        if (
            !is_string($value)
            || !in_array($value, self::FRESHNESS_STATUSES, true)
        ) {
            throw new BadRequest(
                'FeedbackLearningObservation has an invalid freshnessStatus.'
            );
        }

        return $value;
    }

    private function initialStatus(mixed $value): string
    {
        if ($value !== null && $value !== 'OBSERVED') {
            throw new BadRequest(
                'FeedbackLearningObservation new records must be OBSERVED.'
            );
        }

        return 'OBSERVED';
    }
}
