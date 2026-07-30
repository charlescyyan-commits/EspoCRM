<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates and governs immutable, advisory reply-interpretation records.
 *
 * Source references are retained as provenance only. This service never
 * resolves or mutates C22 records, creates commercial records, or triggers
 * execution.
 */
final class ReplySignalService
{
    public const ENTITY_TYPE = 'ReplySignal';
    public const STATUS_RECEIVED = 'RECEIVED';
    public const STATUS_INTERPRETED = 'INTERPRETED';
    public const STATUS_REVIEWED = 'REVIEWED';
    public const STATUS_CONVERTED = 'CONVERTED';
    public const STATUS_DISMISSED = 'DISMISSED';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'sourceReference',
        'provenance',
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

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {
    }

    /** @param array<string, mixed> $attributes */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }

        $attributes = $this->validate($attributes);
        $signal = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $signal->set([
            'name' => 'Reply Signal: ' . $attributes['sourceReference']['reference'],
            'sourceReference' => json_encode(
                $attributes['sourceReference'],
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'provenance' => $attributes['provenance'],
            'freshnessStatus' => $attributes['freshnessStatus'],
            'status' => self::STATUS_RECEIVED,
            'lifecycleAudit' => json_encode([
                $this->auditEntry(null, self::STATUS_RECEIVED, null),
            ], JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE),
        ]);
        $this->entityManager->saveEntity($signal, [
            C24ReplySignalSaveOption::REPLY_SIGNAL_CREATE_AUTHORIZED => true,
        ]);

        return $signal;
    }

    public function interpret(
        string $id,
        string $interpretation,
        int|float $confidence
    ): Entity {
        return $this->transition(
            $id,
            self::STATUS_RECEIVED,
            self::STATUS_INTERPRETED,
            [
                'interpretation' => $this->advisoryInterpretation($interpretation),
                'confidence' => $this->confidence($confidence),
            ]
        );
    }

    public function review(string $id, ?string $decisionNote = null): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_INTERPRETED,
            self::STATUS_REVIEWED,
            [],
            $decisionNote
        );
    }

    public function convert(string $id, ?string $decisionNote = null): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_CONVERTED,
            [],
            $decisionNote
        );
    }

    public function dismiss(string $id, string $decisionNote): Entity
    {
        $decisionNote = $this->requiredText($decisionNote, 'decisionNote');

        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_DISMISSED,
            [],
            $decisionNote
        );
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $signal = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$signal || $signal->isNew()) {
            throw new BadRequest('ReplySignal does not exist.');
        }
        if (!$this->acl->checkEntityRead($signal)) {
            throw new Forbidden();
        }

        return $signal;
    }

    /** @param array<string, mixed> $attributes */
    public function validate(array $attributes): array
    {
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest('ReplySignal contains unsupported fields.');
        }

        return [
            'sourceReference' => $this->sourceReference(
                $attributes['sourceReference'] ?? null
            ),
            'provenance' => $this->requiredText(
                $attributes['provenance'] ?? null,
                'provenance'
            ),
            'freshnessStatus' => $this->freshnessStatus(
                $attributes['freshnessStatus'] ?? null
            ),
            'status' => $this->initialStatus($attributes['status'] ?? null),
        ];
    }

    /**
     * @param array<string, mixed> $changes
     */
    private function transition(
        string $id,
        string $expectedStatus,
        string $targetStatus,
        array $changes,
        ?string $decisionNote = null
    ): Entity {
        $signal = $this->read($id);
        if (!$this->acl->checkEntityEdit($signal)) {
            throw new Forbidden();
        }
        if ((string) $signal->get('status') !== $expectedStatus) {
            throw new Conflict(
                "ReplySignal must be {$expectedStatus} before {$targetStatus}."
            );
        }

        $actor = $this->authenticatedHumanReference();
        $audit = $this->lifecycleAudit($signal);
        $audit[] = $this->auditEntry($expectedStatus, $targetStatus, $actor);
        $signal->set([
            ...$changes,
            'status' => $targetStatus,
            'transitionedAt' => (new DateTimeImmutable())->format('Y-m-d H:i:s'),
            'transitionedByReference' => $actor,
            'decisionNote' => $this->optionalText($decisionNote),
            'lifecycleAudit' => json_encode(
                $audit,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
        ]);
        $this->entityManager->saveEntity($signal, [
            C24ReplySignalSaveOption::LIFECYCLE_MUTATION_AUTHORIZED => true,
        ]);

        return $signal;
    }

    /** @return array{entityType: string, reference: string} */
    private function sourceReference(mixed $value): array
    {
        if (!is_array($value)) {
            throw new BadRequest('ReplySignal requires a C22 sourceReference.');
        }
        $entityType = $value['entityType'] ?? null;
        $reference = $value['reference'] ?? null;
        if (
            $entityType !== 'ReplyDetection'
            || !is_string($reference)
            || trim($reference) === ''
        ) {
            throw new BadRequest(
                'ReplySignal sourceReference must be a ReplyDetection reference.'
            );
        }

        return [
            'entityType' => 'ReplyDetection',
            'reference' => trim($reference),
        ];
    }

    /** @return list<array<string, ?string>> */
    private function lifecycleAudit(Entity $signal): array
    {
        $value = $signal->get('lifecycleAudit');
        if (!is_string($value) || trim($value) === '') {
            throw new Conflict('ReplySignal lifecycle audit is missing.');
        }
        try {
            $audit = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Conflict('ReplySignal lifecycle audit is invalid.');
        }
        if (!is_array($audit) || $audit === []) {
            throw new Conflict('ReplySignal lifecycle audit is invalid.');
        }

        return $audit;
    }

    /** @return array{from: ?string, to: string, at: string, actor: ?string} */
    private function auditEntry(?string $from, string $to, ?string $actor): array
    {
        return [
            'from' => $from,
            'to' => $to,
            'at' => (new DateTimeImmutable())->format('Y-m-d H:i:s'),
            'actor' => $actor,
        ];
    }

    private function advisoryInterpretation(string $value): string
    {
        $value = $this->requiredText($value, 'interpretation');
        if (preg_match(
            '/^(send|execute|approve|create|trigger|apply|route|schedule)\\b/i',
            $value
        ) === 1) {
            throw new BadRequest('ReplySignal interpretation must be advisory.');
        }

        return $value;
    }

    private function confidence(mixed $value): float
    {
        if (
            (!is_int($value) && !is_float($value))
            || $value < 0
            || $value > 1
        ) {
            throw new BadRequest('ReplySignal confidence must be between 0 and 1.');
        }

        return (float) $value;
    }

    private function freshnessStatus(mixed $value): string
    {
        if (!is_string($value) || !in_array($value, self::FRESHNESS_STATUSES, true)) {
            throw new BadRequest('ReplySignal has an invalid freshnessStatus.');
        }

        return $value;
    }

    private function initialStatus(mixed $value): string
    {
        if ($value !== null && $value !== self::STATUS_RECEIVED) {
            throw new BadRequest('New ReplySignal records must be RECEIVED.');
        }

        return self::STATUS_RECEIVED;
    }

    private function authenticatedHumanReference(): string
    {
        $reference = $this->optionalText($this->user->getId());
        if ($reference === null) {
            throw new Forbidden('ReplySignal transition requires an authenticated human.');
        }

        return $reference;
    }

    private function requiredText(mixed $value, string $field): string
    {
        if (!is_string($value) || trim($value) === '') {
            throw new BadRequest("ReplySignal requires {$field}.");
        }

        return trim($value);
    }

    private function optionalText(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
