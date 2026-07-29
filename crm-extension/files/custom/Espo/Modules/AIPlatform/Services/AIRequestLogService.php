<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Appends validated, metadata-only evidence for an AI execution attempt.
 *
 * This service does not execute AI, resolve a provider, make network calls,
 * schedule retries, or persist request and response payloads.
 */
final class AIRequestLogService
{
    public const ENTITY_TYPE = 'AIRequestLog';

    public const STATUS_SUCCEEDED = 'SUCCEEDED';
    public const STATUS_FAILED = 'FAILED';

    /** @var list<string> */
    private const CAPABILITIES = ['SEARCH', 'ENRICHMENT', 'COMPLETION'];

    /** @var list<string> */
    private const FAILURE_CATEGORIES = [
        'NETWORK',
        'PROVIDER',
        'AUTH',
        'RATE_LIMIT',
        'VALIDATION',
        'UNKNOWN',
        'QUOTA',
        'CONTENT_FILTER',
    ];

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'name',
        'aiJobId',
        'attemptId',
        'attemptNumber',
        'capability',
        'purpose',
        'provider',
        'model',
        'promptTemplateId',
        'promptTemplateVersion',
        'promptTemplateHash',
        'inputTokens',
        'outputTokens',
        'totalTokens',
        'costAmount',
        'costCurrency',
        'latencyMs',
        'status',
        'errorClass',
        'failureCategory',
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private PromptTemplateService $promptTemplateService,
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

        $this->assertCreateAttributes($attributes);
        $aiJob = $this->entityManager->getEntity('AIJob', (string) $attributes['aiJobId']);
        if ($aiJob->isNew()) {
            throw new BadRequest('AIRequestLog aiJobId must reference an existing AIJob.');
        }
        $template = $this->assertPromptTemplateProvenance($attributes);

        $log = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $log->set([
            'name' => $this->requiredString($attributes, 'name'),
            'aiJobId' => (string) $aiJob->getId(),
            'attemptId' => $this->requiredString($attributes, 'attemptId'),
            'attemptNumber' => $this->positiveInt($attributes, 'attemptNumber'),
            'capability' => $this->requiredCapability($attributes),
            'purpose' => $this->requiredString($attributes, 'purpose'),
            'provider' => $this->requiredString($attributes, 'provider'),
            'model' => $this->requiredString($attributes, 'model'),
            'promptTemplateId' => $this->requiredString($attributes, 'promptTemplateId'),
            'promptTemplateVersion' => $this->positiveInt($attributes, 'promptTemplateVersion'),
            'promptTemplateHash' => $this->requiredHash($attributes, 'promptTemplateHash'),
            'inputTokens' => $this->nonNegativeInt($attributes, 'inputTokens'),
            'outputTokens' => $this->nonNegativeInt($attributes, 'outputTokens'),
            'totalTokens' => $this->nonNegativeInt($attributes, 'totalTokens'),
            'costAmount' => $this->nonNegativeNumber($attributes, 'costAmount'),
            'costCurrency' => $this->requiredCurrency($attributes),
            'latencyMs' => $this->nonNegativeInt($attributes, 'latencyMs'),
            'status' => (string) $attributes['status'],
            'errorClass' => $this->optionalString($attributes['errorClass'] ?? null),
            'failureCategory' => $this->optionalString($attributes['failureCategory'] ?? null),
        ]);

        $this->entityManager->getTransactionManager()->run(
            function () use ($log, $template): void {
                $this->entityManager->saveEntity($log, [
                    AIRequestLogSaveOption::AI_REQUEST_LOG_CREATE_AUTHORIZED => true,
                ]);
                $this->promptTemplateService->markReferenced($template);
            }
        );

        return $log;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function assertCreateAttributes(array $attributes): void
    {
        if (array_diff(array_keys($attributes), self::CREATE_FIELDS) !== []) {
            throw new BadRequest('AIRequestLog create contains unsupported fields.');
        }

        foreach ([
            'name', 'aiJobId', 'attemptId', 'capability', 'purpose', 'provider',
            'model', 'promptTemplateId', 'promptTemplateHash', 'costCurrency',
        ] as $field) {
            $this->requiredString($attributes, $field);
        }
        foreach (['attemptNumber', 'promptTemplateVersion'] as $field) {
            $this->positiveInt($attributes, $field);
        }
        foreach (['inputTokens', 'outputTokens', 'totalTokens', 'latencyMs'] as $field) {
            $this->nonNegativeInt($attributes, $field);
        }
        $this->nonNegativeNumber($attributes, 'costAmount');

        if ($this->nonNegativeInt($attributes, 'totalTokens') !== (
            $this->nonNegativeInt($attributes, 'inputTokens')
            + $this->nonNegativeInt($attributes, 'outputTokens')
        )) {
            throw new BadRequest('AIRequestLog totalTokens must equal inputTokens plus outputTokens.');
        }
        if (!in_array($attributes['status'] ?? null, [self::STATUS_SUCCEEDED, self::STATUS_FAILED], true)) {
            throw new BadRequest('AIRequestLog create has an unsupported status.');
        }

        $failureCategory = $this->optionalString($attributes['failureCategory'] ?? null);
        if ($failureCategory !== null && !in_array($failureCategory, self::FAILURE_CATEGORIES, true)) {
            throw new BadRequest('AIRequestLog create has an unsupported failureCategory.');
        }
        if ((string) $attributes['status'] === self::STATUS_SUCCEEDED && ($failureCategory !== null || $this->optionalString($attributes['errorClass'] ?? null) !== null)) {
            throw new BadRequest('AIRequestLog SUCCEEDED evidence cannot contain failure metadata.');
        }
        if ((string) $attributes['status'] === self::STATUS_FAILED && $failureCategory === null) {
            throw new BadRequest('AIRequestLog FAILED evidence requires failureCategory.');
        }
    }

    /**
     * Checks only the prompt provenance tuple. Template content is never read
     * into this evidence record.
     *
     * @param array<string, mixed> $attributes
     */
    private function assertPromptTemplateProvenance(array $attributes): Entity
    {
        $template = $this->entityManager->getEntity(
            PromptTemplateService::ENTITY_TYPE,
            $this->requiredString($attributes, 'promptTemplateId')
        );
        if ($template->isNew()) {
            throw new BadRequest(
                'AIRequestLog promptTemplateId must reference an existing PromptTemplate.'
            );
        }
        if (
            (int) $template->get('version') !== $this->positiveInt($attributes, 'promptTemplateVersion')
            || (string) $template->get('contentHash') !== $this->requiredHash($attributes, 'promptTemplateHash')
        ) {
            throw new BadRequest(
                'AIRequestLog prompt provenance must match the referenced PromptTemplate version and hash.'
            );
        }

        return $template;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredCapability(array $attributes): string
    {
        $capability = $this->requiredString($attributes, 'capability');
        if (!in_array($capability, self::CAPABILITIES, true)) {
            throw new BadRequest('AIRequestLog create has an unsupported capability.');
        }

        return $capability;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredHash(array $attributes, string $field): string
    {
        $hash = $this->requiredString($attributes, $field);
        if (!preg_match('/^[a-f0-9]{64}$/', $hash)) {
            throw new BadRequest("AIRequestLog {$field} must be a SHA-256 hex digest.");
        }

        return $hash;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredCurrency(array $attributes): string
    {
        $currency = strtoupper($this->requiredString($attributes, 'costCurrency'));
        if (!preg_match('/^[A-Z]{3}$/', $currency)) {
            throw new BadRequest('AIRequestLog costCurrency must be an ISO 4217 code.');
        }

        return $currency;
    }

    /** @param array<string, mixed> $attributes */
    private function requiredString(array $attributes, string $field): string
    {
        $value = $this->optionalString($attributes[$field] ?? null);
        if ($value === null) {
            throw new BadRequest("AIRequestLog create requires {$field}.");
        }

        return $value;
    }

    /** @param array<string, mixed> $attributes */
    private function positiveInt(array $attributes, string $field): int
    {
        $value = $attributes[$field] ?? null;
        if (!is_int($value) || $value < 1) {
            throw new BadRequest("AIRequestLog {$field} must be a positive integer.");
        }

        return $value;
    }

    /** @param array<string, mixed> $attributes */
    private function nonNegativeInt(array $attributes, string $field): int
    {
        $value = $attributes[$field] ?? null;
        if (!is_int($value) || $value < 0) {
            throw new BadRequest("AIRequestLog {$field} must be a non-negative integer.");
        }

        return $value;
    }

    /** @param array<string, mixed> $attributes */
    private function nonNegativeNumber(array $attributes, string $field): float
    {
        $value = $attributes[$field] ?? null;
        if ((!is_int($value) && !is_float($value)) || $value < 0) {
            throw new BadRequest("AIRequestLog {$field} must be a non-negative number.");
        }

        return (float) $value;
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
