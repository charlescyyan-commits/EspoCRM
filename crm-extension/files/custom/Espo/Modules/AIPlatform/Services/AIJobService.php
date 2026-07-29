<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Lifecycle-only service for one controlled AI execution record.
 *
 * This skeleton creates and validates AIJob records. It does not resolve a
 * capability, invoke an adapter, dispatch a worker, or perform any I/O.
 */
final class AIJobService
{
    public const ENTITY_TYPE = 'AIJob';

    public const STATUS_QUEUED = 'QUEUED';
    public const STATUS_RUNNING = 'RUNNING';
    public const STATUS_SUCCEEDED = 'SUCCEEDED';
    public const STATUS_FAILED = 'FAILED';
    public const STATUS_CANCELLED = 'CANCELLED';

    public const EXECUTION_MODE_LIVE = 'LIVE';
    public const EXECUTION_MODE_DRY_RUN = 'DRY_RUN';

    /** @var list<string> */
    private const CAPABILITIES = ['SEARCH', 'ENRICHMENT', 'COMPLETION'];

    /** @var array<string, list<string>> */
    private const VALID_TRANSITIONS = [
        self::STATUS_QUEUED => [self::STATUS_RUNNING, self::STATUS_CANCELLED],
        self::STATUS_RUNNING => [
            self::STATUS_SUCCEEDED,
            self::STATUS_FAILED,
            self::STATUS_CANCELLED,
        ],
        self::STATUS_FAILED => [self::STATUS_QUEUED],
        self::STATUS_SUCCEEDED => [],
        self::STATUS_CANCELLED => [],
    ];

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'name',
        'capability',
        'purpose',
        'requestedById',
        'policyVersion',
        'executionMode',
        'idempotencyKey',
        'resultReference',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    /**
     * @param array<string, mixed> $attributes
     */
    public function create(array $attributes): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden();
        }

        $this->assertCreateAttributes($attributes);
        $existing = $this->findExistingIdempotencyKey((string) $attributes['idempotencyKey']);
        if ($existing instanceof Entity) {
            $this->assertEquivalentIdempotencyContext($existing, $attributes);

            return $existing;
        }

        $job = $this->entityManager->getEntity(self::ENTITY_TYPE);
        $job->set([
            'name' => trim((string) $attributes['name']),
            'capability' => (string) $attributes['capability'],
            'purpose' => trim((string) $attributes['purpose']),
            'requestedById' => trim((string) $attributes['requestedById']),
            'policyVersion' => trim((string) $attributes['policyVersion']),
            'executionMode' => $attributes['executionMode'] ?? self::EXECUTION_MODE_LIVE,
            'idempotencyKey' => trim((string) $attributes['idempotencyKey']),
            'resultReference' => $this->optionalString($attributes['resultReference'] ?? null),
            'status' => self::STATUS_QUEUED,
            'attemptCount' => 0,
        ]);

        $this->entityManager->saveEntity($job, [
            AIJobStatusMutationSaveOption::AI_JOB_STATUS_MUTATION_AUTHORIZED => true,
        ]);

        return $job;
    }

    public function validateTransition(string $currentStatus, string $targetStatus): bool
    {
        $this->assertKnownStatus($currentStatus);
        $this->assertKnownStatus($targetStatus);

        return in_array($targetStatus, self::VALID_TRANSITIONS[$currentStatus], true);
    }

    /**
     * @param array{now?: DateTimeImmutable|string} $options
     */
    public function transition(Entity $job, string $targetStatus, array $options = []): Entity
    {
        $this->assertEntityType($job);
        if (!$this->acl->checkEntityEdit($job)) {
            throw new Forbidden();
        }

        $currentStatus = (string) ($job->get('status') ?: self::STATUS_QUEUED);
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("AIJob transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        $now = $this->resolveNow($options);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($job, $currentStatus, $targetStatus, $now): Entity {
                if ($targetStatus === self::STATUS_RUNNING) {
                    $job->set('startedAt', $now->format('Y-m-d H:i:s'));
                    $job->set('attemptCount', (int) ($job->get('attemptCount') ?? 0) + 1);
                }
                if (in_array($targetStatus, [self::STATUS_SUCCEEDED, self::STATUS_CANCELLED], true)) {
                    $job->set('completedAt', $now->format('Y-m-d H:i:s'));
                }

                $job->set('status', $targetStatus);
                $this->entityManager->saveEntity($job, [
                    AIJobStatusMutationSaveOption::AI_JOB_STATUS_MUTATION_AUTHORIZED => true,
                ]);

                return $job;
            }
        );
    }

    private function findExistingIdempotencyKey(string $idempotencyKey): ?Entity
    {
        $existing = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['idempotencyKey' => $idempotencyKey])
            ->findOne();

        return $existing instanceof Entity ? $existing : null;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function assertCreateAttributes(array $attributes): void
    {
        $unknownFields = array_diff(array_keys($attributes), self::CREATE_FIELDS);
        if ($unknownFields !== []) {
            throw new BadRequest('AIJob create contains unsupported fields.');
        }

        foreach (['name', 'capability', 'purpose', 'requestedById', 'policyVersion', 'idempotencyKey'] as $field) {
            if (trim((string) ($attributes[$field] ?? '')) === '') {
                throw new BadRequest("AIJob create requires {$field}.");
            }
        }

        if (!in_array($attributes['capability'], self::CAPABILITIES, true)) {
            throw new BadRequest('AIJob create has an unsupported capability.');
        }

        $executionMode = $attributes['executionMode'] ?? self::EXECUTION_MODE_LIVE;
        if (!in_array($executionMode, [self::EXECUTION_MODE_LIVE, self::EXECUTION_MODE_DRY_RUN], true)) {
            throw new BadRequest('AIJob create has an unsupported executionMode.');
        }
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function assertEquivalentIdempotencyContext(Entity $existing, array $attributes): void
    {
        $expected = [
            'capability' => (string) $attributes['capability'],
            'purpose' => trim((string) $attributes['purpose']),
            'requestedById' => trim((string) $attributes['requestedById']),
            'policyVersion' => trim((string) $attributes['policyVersion']),
            'executionMode' => (string) ($attributes['executionMode'] ?? self::EXECUTION_MODE_LIVE),
        ];
        foreach ($expected as $field => $value) {
            if ((string) $existing->get($field) !== $value) {
                throw new Conflict('AIJob idempotency key belongs to a different execution context.');
            }
        }
    }

    /**
     * @param array{now?: DateTimeImmutable|string} $options
     */
    private function resolveNow(array $options): DateTimeImmutable
    {
        $now = $options['now'] ?? new DateTimeImmutable();
        if (is_string($now)) {
            $now = new DateTimeImmutable($now);
        }
        if (!$now instanceof DateTimeImmutable) {
            throw new BadRequest('Invalid AIJob transition clock.');
        }

        return $now;
    }

    private function assertKnownStatus(string $status): void
    {
        if (!array_key_exists($status, self::VALID_TRANSITIONS)) {
            throw new BadRequest("Unknown AIJob status: {$status}.");
        }
    }

    private function assertEntityType(Entity $job): void
    {
        if ($job->getEntityType() !== self::ENTITY_TYPE) {
            throw new BadRequest('AIJob lifecycle requires an AIJob entity.');
        }
    }

    private function optionalString(mixed $value): ?string
    {
        $value = trim((string) $value);

        return $value === '' ? null : $value;
    }
}
