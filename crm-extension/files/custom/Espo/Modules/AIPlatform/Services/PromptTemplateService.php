<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Governance service for versioned prompt templates.
 *
 * This service does not render prompts, resolve providers, or dispatch work.
 */
final class PromptTemplateService
{
    public const ENTITY_TYPE = 'PromptTemplate';

    public const STATUS_DRAFT = 'DRAFT';
    public const STATUS_ACTIVE = 'ACTIVE';
    public const STATUS_RETIRED = 'RETIRED';

    public const GOVERNANCE_MARKER = 'c20-prompt-template-governance-v1';

    /** @var list<string> */
    public const IMMUTABLE_AFTER_REFERENCE_FIELDS = [
        'templateKey',
        'version',
        'contentHash',
        'templateBody',
    ];

    /** @var array<string, list<string>> */
    private const VALID_TRANSITIONS = [
        self::STATUS_DRAFT => [self::STATUS_ACTIVE],
        self::STATUS_ACTIVE => [self::STATUS_RETIRED],
        self::STATUS_RETIRED => [],
    ];

    public function __construct(private EntityManager $entityManager)
    {
    }

    /**
     * @param array{
     *   name: string,
     *   templateKey: string,
     *   version: int,
     *   capability: string,
     *   purpose: string,
     *   templateBody: string
     * } $data
     */
    public function createTemplate(array $data): Entity
    {
        $name = $this->requiredString($data, 'name');
        $templateKey = $this->normalizeTemplateKey(
            $this->requiredString($data, 'templateKey')
        );
        $version = $this->requiredVersion($data['version'] ?? null);
        $capability = $this->requiredString($data, 'capability');
        $purpose = $this->requiredString($data, 'purpose');
        $templateBody = $this->requiredString($data, 'templateBody', false);

        $this->assertVersionAvailable($templateKey, $version);

        $template = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $template->set([
            'name' => $name,
            'templateKey' => $templateKey,
            'version' => $version,
            'contentHash' => self::hashContent($templateBody),
            'capability' => $capability,
            'purpose' => $purpose,
            'templateBody' => $templateBody,
            'status' => self::STATUS_DRAFT,
            'hasBeenReferenced' => false,
        ]);
        $this->entityManager->saveEntity($template);

        return $template;
    }

    /**
     * @param array{
     *   name?: string,
     *   capability?: string,
     *   purpose?: string
     * } $overrides
     */
    public function createNewVersion(
        Entity $source,
        int $version,
        string $templateBody,
        array $overrides = []
    ): Entity {
        $this->assertPromptTemplate($source);
        $currentVersion = (int) $source->get('version');
        if ($version <= $currentVersion) {
            throw new BadRequest(
                'A new PromptTemplate version must be greater than its source version.'
            );
        }

        return $this->createTemplate([
            'name' => $overrides['name'] ?? (string) $source->get('name'),
            'templateKey' => (string) $source->get('templateKey'),
            'version' => $version,
            'capability' => $overrides['capability'] ?? (string) $source->get('capability'),
            'purpose' => $overrides['purpose'] ?? (string) $source->get('purpose'),
            'templateBody' => $templateBody,
        ]);
    }

    public function updateDraftContent(Entity $template, string $templateBody): Entity
    {
        $this->assertPromptTemplate($template);
        if ((string) $template->get('status') !== self::STATUS_DRAFT) {
            throw new Forbidden(
                'Only a DRAFT PromptTemplate may have its content updated.'
            );
        }
        if ((bool) $template->get('hasBeenReferenced')) {
            throw new Forbidden(
                'A referenced PromptTemplate version is immutable.'
            );
        }

        if (trim($templateBody) === '') {
            throw new BadRequest('PromptTemplate templateBody is required.');
        }

        $template->set('templateBody', $templateBody);
        $template->set('contentHash', self::hashContent($templateBody));
        $this->entityManager->saveEntity($template);

        return $template;
    }

    public function activate(Entity $template): Entity
    {
        return $this->transition($template, self::STATUS_ACTIVE);
    }

    public function retire(Entity $template): Entity
    {
        return $this->transition($template, self::STATUS_RETIRED);
    }

    public function validateTransition(string $currentStatus, string $targetStatus): bool
    {
        $this->assertKnownStatus($currentStatus);
        $this->assertKnownStatus($targetStatus);

        return in_array($targetStatus, self::VALID_TRANSITIONS[$currentStatus], true);
    }

    public function transition(Entity $template, string $targetStatus): Entity
    {
        $this->assertPromptTemplate($template);
        $currentStatus = (string) ($template->get('status') ?: self::STATUS_DRAFT);
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest(
                "PromptTemplate transition {$currentStatus} -> {$targetStatus} is not allowed."
            );
        }

        $template->set('status', $targetStatus);
        $this->entityManager->saveEntity($template, [
            PromptTemplateSaveOption::LIFECYCLE_MUTATION_AUTHORIZED => true,
        ]);

        return $template;
    }

    /**
     * Marks an ACTIVE version as having execution evidence without depending
     * on the evidence entity. WP3.2 may call this boundary after it persists
     * its append-only record.
     */
    public function markReferenced(Entity $template): Entity
    {
        $this->assertPromptTemplate($template);
        if ((string) $template->get('status') !== self::STATUS_ACTIVE) {
            throw new BadRequest(
                'Only an ACTIVE PromptTemplate may accept a new execution reference.'
            );
        }

        if ((bool) $template->get('hasBeenReferenced')) {
            return $template;
        }

        $template->set('hasBeenReferenced', true);
        $this->entityManager->saveEntity($template, [
            PromptTemplateSaveOption::REFERENCE_MARK_AUTHORIZED => true,
        ]);

        return $template;
    }

    public static function assertImmutableFieldsUnchanged(Entity $template): void
    {
        $fetchedStatus = (string) $template->getFetched('status');
        $governedStatus = in_array(
            $fetchedStatus,
            [self::STATUS_ACTIVE, self::STATUS_RETIRED],
            true
        );
        $referenced = (bool) $template->getFetched('hasBeenReferenced')
            || (bool) $template->get('hasBeenReferenced');
        if (!$governedStatus || !$referenced) {
            return;
        }

        foreach (self::IMMUTABLE_AFTER_REFERENCE_FIELDS as $field) {
            if ($template->isAttributeChanged($field)) {
                throw new Forbidden(
                    "Referenced PromptTemplate field {$field} is immutable; create a new version."
                );
            }
        }
    }

    public static function hashContent(string $templateBody): string
    {
        return hash('sha256', $templateBody);
    }

    private function assertVersionAvailable(string $templateKey, int $version): void
    {
        $existing = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where([
                'templateKey' => $templateKey,
                'version' => $version,
            ])
            ->findOne();

        if ($existing instanceof Entity) {
            throw new Conflict(
                "PromptTemplate {$templateKey} version {$version} already exists."
            );
        }
    }

    /**
     * @param array<string, mixed> $data
     */
    private function requiredString(array $data, string $field, bool $trim = true): string
    {
        $value = $data[$field] ?? null;
        if (!is_string($value)) {
            throw new BadRequest("PromptTemplate {$field} is required.");
        }

        $normalizedValue = trim($value);
        if ($normalizedValue === '') {
            throw new BadRequest("PromptTemplate {$field} is required.");
        }

        return $trim ? $normalizedValue : $value;
    }

    private function requiredVersion(mixed $value): int
    {
        if (!is_int($value) || $value < 1) {
            throw new BadRequest('PromptTemplate version must be a positive integer.');
        }

        return $value;
    }

    private function normalizeTemplateKey(string $templateKey): string
    {
        if (!preg_match('/^[a-z][a-z0-9_]*$/', $templateKey)) {
            throw new BadRequest(
                'PromptTemplate templateKey must use lower snake_case.'
            );
        }

        return $templateKey;
    }

    private function assertPromptTemplate(Entity $template): void
    {
        if ($template->getEntityType() !== self::ENTITY_TYPE) {
            throw new BadRequest(
                'PromptTemplate governance requires a PromptTemplate entity.'
            );
        }
    }

    private function assertKnownStatus(string $status): void
    {
        if (!array_key_exists($status, self::VALID_TRANSITIONS)) {
            throw new BadRequest("Unknown PromptTemplate status: {$status}.");
        }
    }
}
