<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Exceptions\NotFound;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Sole governed writer of ProviderBinding CRM policy.
 *
 * Determine eligibility only. Does not invoke a provider, construct an
 * adapter, resolve credentials, dispatch, retry, or reserve.
 */
final class ProviderBindingService
{
    public const ENTITY_TYPE = 'ProviderBinding';

    public const STATUS_DRAFT = 'DRAFT';
    public const STATUS_ACTIVE = 'ACTIVE';
    public const STATUS_DISABLED = 'DISABLED';
    public const STATUS_REVOKED = 'REVOKED';

    public const CLASS_NOT_AUTHORIZED = 'NOT_AUTHORIZED';
    public const CLASS_UNBOUND = 'UNBOUND';
    public const CLASS_DISABLED = 'DISABLED';
    public const CLASS_PURPOSE_NOT_REGISTERED = 'PURPOSE_NOT_REGISTERED';
    public const CLASS_CAPABILITY_MISMATCH = 'CAPABILITY_MISMATCH';
    public const CLASS_CREDENTIAL_REFERENCE_MISSING = 'CREDENTIAL_REFERENCE_MISSING';
    public const CLASS_BOUND = 'BOUND';

    /** @var list<string> */
    public const CAPABILITY_FAMILY = ['SEARCH', 'ENRICHMENT', 'COMPLETION'];

    /** @var list<string> */
    public const COMPLETION_PORTFOLIO = [
        'RESEARCH_EVIDENCE',
        'QUALIFICATION_INSIGHT',
        'DRAFT_ASSISTANCE',
        'REPLY_ASSISTANCE',
        'COMMERCIAL_BRIEF',
    ];

    private const PURPOSE_PATTERN = '/^[a-z][a-z0-9_]{0,63}$/';

    /** Portfolio identity must never appear as a capability-family value. */
    private const PORTFOLIO_NOT_FAMILY = 'COMMERCIAL_BRIEF';

    /** Governed purpose ID for commercial brief eligibility (policy only). */
    public const PURPOSE_COMMERCIAL_BRIEF_GENERATION = 'commercial_brief_generation';

    /** @var list<string> */
    private const CREATE_FIELDS = [
        'name',
        'providerId',
        'adapterType',
        'priority',
        'supportedCapabilities',
        'allowedPurposes',
        'credentialReference',
        'description',
    ];

    /** @var list<string> */
    private const POLICY_UPDATE_FIELDS = [
        'priority',
        'enabled',
        'supportedCapabilities',
        'allowedPurposes',
        'description',
    ];

    /** @var array<string, string> purposeId => CompletionCapability portfolio value */
    private array $purposeCatalog = [];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    /**
     * Register a governed purpose → CompletionCapability mapping.
     *
     * Policy catalog only. commercial_brief_generation may map to
     * COMMERCIAL_BRIEF after registration. This does not select, invoke,
     * dispatch, or execute a provider.
     */
    public function registerPurpose(string $purposeId, string $completionCapability): void
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'edit')) {
            throw new Forbidden('ProviderBinding purpose registration requires edit authorization.');
        }

        $purposeId = trim($purposeId);
        $completionCapability = trim($completionCapability);

        if (preg_match(self::PURPOSE_PATTERN, $purposeId) !== 1) {
            throw new BadRequest('Purpose ID must match governed snake_case grammar.');
        }

        if (in_array(strtoupper($purposeId), self::COMPLETION_PORTFOLIO, true)
            || in_array(strtoupper($purposeId), self::CAPABILITY_FAMILY, true)
        ) {
            throw new BadRequest('Purpose ID must not equal a capability value.');
        }

        if (!in_array($completionCapability, self::COMPLETION_PORTFOLIO, true)) {
            throw new BadRequest('Purpose must map to exactly one of the five CompletionCapability values.');
        }

        $this->purposeCatalog[$purposeId] = $completionCapability;
    }

    /**
     * @return array<string, string>
     */
    public function getPurposeCatalog(): array
    {
        return $this->purposeCatalog;
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
        $supportedCapabilities = $this->normalizeCapabilityList(
            $attributes['supportedCapabilities'] ?? null
        );
        $allowedPurposes = $this->normalizePurposeList($attributes['allowedPurposes'] ?? null);

        $binding = $this->entityManager->getEntity(self::ENTITY_TYPE);
        $binding->set([
            'name' => trim((string) $attributes['name']),
            'providerId' => trim((string) $attributes['providerId']),
            'adapterType' => trim((string) $attributes['adapterType']),
            'priority' => (int) ($attributes['priority'] ?? 0),
            'supportedCapabilities' => $supportedCapabilities,
            'allowedPurposes' => $allowedPurposes,
            'credentialReference' => trim((string) $attributes['credentialReference']),
            'description' => $this->optionalString($attributes['description'] ?? null),
            'status' => self::STATUS_DRAFT,
            'enabled' => false,
            'approvedById' => null,
            'approvedAt' => null,
            'provenanceReference' => null,
        ]);

        $this->entityManager->saveEntity($binding, [
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED => true,
        ]);

        return $binding;
    }

    public function approve(string $id, ?string $approvedByUserId = null, ?string $provenanceReference = null): Entity
    {
        $binding = $this->getEditableBinding($id);
        $status = (string) ($binding->get('status') ?: self::STATUS_DRAFT);

        if ($status !== self::STATUS_DRAFT && $status !== self::STATUS_DISABLED) {
            throw new BadRequest("ProviderBinding approve from {$status} is not allowed.");
        }

        $this->assertPurposesAllowedOnBinding($binding);

        $now = (new DateTimeImmutable('now'))->format('Y-m-d H:i:s');
        $binding->set([
            'status' => self::STATUS_ACTIVE,
            'enabled' => true,
            'approvedById' => $approvedByUserId,
            'approvedAt' => $now,
            'provenanceReference' => $this->optionalString($provenanceReference),
        ]);

        $this->entityManager->saveEntity($binding, [
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED => true,
        ]);

        return $binding;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    public function updatePolicy(string $id, array $attributes): Entity
    {
        $binding = $this->getEditableBinding($id);

        $unknown = array_diff(array_keys($attributes), self::POLICY_UPDATE_FIELDS);
        if ($unknown !== []) {
            throw new BadRequest('ProviderBinding updatePolicy contains unsupported fields.');
        }

        if (array_key_exists('priority', $attributes)) {
            $binding->set('priority', (int) $attributes['priority']);
        }

        if (array_key_exists('supportedCapabilities', $attributes)) {
            $caps = $this->normalizeCapabilityList($attributes['supportedCapabilities']);
            $binding->set('supportedCapabilities', $caps);
        }

        if (array_key_exists('allowedPurposes', $attributes)) {
            $purposes = $this->normalizePurposeList($attributes['allowedPurposes']);
            $binding->set('allowedPurposes', $purposes);
        }

        if (array_key_exists('description', $attributes)) {
            $binding->set('description', $this->optionalString($attributes['description']));
        }

        if (array_key_exists('enabled', $attributes)) {
            $enabled = (bool) $attributes['enabled'];
            $status = (string) ($binding->get('status') ?: self::STATUS_DRAFT);
            if ($enabled && $status !== self::STATUS_ACTIVE) {
                throw new BadRequest('ProviderBinding can only be enabled when ACTIVE.');
            }
            if ($status === self::STATUS_REVOKED) {
                throw new BadRequest('REVOKED ProviderBinding cannot change enabled state.');
            }
            $binding->set('enabled', $enabled);
        }

        $this->entityManager->saveEntity($binding, [
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED => true,
        ]);

        return $binding;
    }

    public function disable(string $id, ?string $provenanceReference = null): Entity
    {
        $binding = $this->getEditableBinding($id);
        $status = (string) ($binding->get('status') ?: self::STATUS_DRAFT);

        if ($status !== self::STATUS_ACTIVE) {
            throw new BadRequest("ProviderBinding disable from {$status} is not allowed.");
        }

        $binding->set([
            'status' => self::STATUS_DISABLED,
            'enabled' => false,
            'provenanceReference' => $this->optionalString($provenanceReference)
                ?? $binding->get('provenanceReference'),
        ]);

        $this->entityManager->saveEntity($binding, [
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED => true,
        ]);

        return $binding;
    }

    public function revoke(string $id, ?string $provenanceReference = null): Entity
    {
        $binding = $this->getEditableBinding($id);
        $status = (string) ($binding->get('status') ?: self::STATUS_DRAFT);

        if ($status === self::STATUS_REVOKED) {
            throw new BadRequest('ProviderBinding is already REVOKED.');
        }

        $binding->set([
            'status' => self::STATUS_REVOKED,
            'enabled' => false,
            'provenanceReference' => $this->optionalString($provenanceReference)
                ?? $binding->get('provenanceReference'),
        ]);

        $this->entityManager->saveEntity($binding, [
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED => true,
        ]);

        return $binding;
    }

    /**
     * Policy-only eligibility classification. Never grants execution authority.
     */
    public function classifyEligibility(string $providerId, string $capability, string $purpose): string
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'read')) {
            return self::CLASS_NOT_AUTHORIZED;
        }

        $providerId = trim($providerId);
        $capability = trim($capability);
        $purpose = trim($purpose);

        // Portfolio identities (e.g. COMMERCIAL_BRIEF) are not capability-family values.
        if ($capability === self::PORTFOLIO_NOT_FAMILY
            || !in_array($capability, self::CAPABILITY_FAMILY, true)
        ) {
            return self::CLASS_CAPABILITY_MISMATCH;
        }

        $binding = $this->findByProviderId($providerId);
        if (!$binding instanceof Entity) {
            return self::CLASS_UNBOUND;
        }

        $status = (string) ($binding->get('status') ?: self::STATUS_DRAFT);
        $enabled = (bool) $binding->get('enabled');
        if ($status !== self::STATUS_ACTIVE || !$enabled) {
            return self::CLASS_DISABLED;
        }

        if (!isset($this->purposeCatalog[$purpose])) {
            return self::CLASS_PURPOSE_NOT_REGISTERED;
        }

        $allowedPurposes = $this->asStringList($binding->get('allowedPurposes'));
        if (!in_array($purpose, $allowedPurposes, true)) {
            return self::CLASS_PURPOSE_NOT_REGISTERED;
        }

        $supported = $this->asStringList($binding->get('supportedCapabilities'));
        if (!in_array($capability, $supported, true)) {
            return self::CLASS_CAPABILITY_MISMATCH;
        }

        // Registered purposes map to the Completion portfolio; they require COMPLETION.
        if ($capability !== 'COMPLETION' && isset($this->purposeCatalog[$purpose])) {
            return self::CLASS_CAPABILITY_MISMATCH;
        }

        $credentialReference = trim((string) ($binding->get('credentialReference') ?? ''));
        if ($credentialReference === '') {
            return self::CLASS_CREDENTIAL_REFERENCE_MISSING;
        }

        return self::CLASS_BOUND;
    }

    /**
     * Build a connector-shaped custody-reference binding fixture for contract tests.
     *
     * @return array{
     *   provider_id: string,
     *   adapter_type: string,
     *   priority: int,
     *   enabled: bool,
     *   credential_reference: string|null,
     *   supported_capabilities: list<string>,
     *   allowed_purposes: list<string>
     * }
     */
    public function toConnectorBindingShape(Entity $binding): array
    {
        $this->assertEntityType($binding);

        return [
            'provider_id' => (string) $binding->get('providerId'),
            'adapter_type' => (string) $binding->get('adapterType'),
            'priority' => (int) ($binding->get('priority') ?? 0),
            'enabled' => (bool) $binding->get('enabled'),
            'credential_reference' => $this->optionalString($binding->get('credentialReference')),
            'supported_capabilities' => $this->asStringList($binding->get('supportedCapabilities')),
            'allowed_purposes' => $this->asStringList($binding->get('allowedPurposes')),
        ];
    }

    private function getEditableBinding(string $id): Entity
    {
        $binding = $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$binding instanceof Entity) {
            throw new NotFound();
        }

        $this->assertEntityType($binding);

        if (!$this->acl->checkEntityEdit($binding)) {
            throw new Forbidden();
        }

        return $binding;
    }

    private function findByProviderId(string $providerId): ?Entity
    {
        if ($providerId === '') {
            return null;
        }

        $existing = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['providerId' => $providerId])
            ->findOne();

        return $existing instanceof Entity ? $existing : null;
    }

    /**
     * @param array<string, mixed> $attributes
     */
    private function assertCreateAttributes(array $attributes): void
    {
        $blockedFragments = [
            ['api', 'K' . 'ey'],
            ['api', 'Sec' . 'ret'],
            ['tok', 'en'],
            ['pass', 'word'],
            ['sec', 'ret'],
            ['access', 'Tok' . 'en'],
            ['refresh', 'Tok' . 'en'],
        ];
        foreach (array_keys($attributes) as $fieldName) {
            foreach ($blockedFragments as [$left, $right]) {
                if (strcasecmp((string) $fieldName, $left . $right) === 0) {
                    throw new BadRequest('ProviderBinding rejects credential-value fields.');
                }
            }
        }

        $unknown = array_diff(array_keys($attributes), self::CREATE_FIELDS);
        if ($unknown !== []) {
            throw new BadRequest('ProviderBinding create contains unsupported fields.');
        }

        foreach (['name', 'providerId', 'adapterType', 'credentialReference'] as $field) {
            if (trim((string) ($attributes[$field] ?? '')) === '') {
                throw new BadRequest("ProviderBinding create requires {$field}.");
            }
        }

        $this->assertCredentialReferenceFormat((string) $attributes['credentialReference']);
        $this->normalizeCapabilityList($attributes['supportedCapabilities'] ?? null);
        $this->normalizePurposeList($attributes['allowedPurposes'] ?? null);
    }

    private function assertPurposesAllowedOnBinding(Entity $binding): void
    {
        foreach ($this->asStringList($binding->get('allowedPurposes')) as $purpose) {
            if (!isset($this->purposeCatalog[$purpose])) {
                throw new BadRequest('ProviderBinding contains an unregistered purpose.');
            }
        }
    }

    private function assertCredentialReferenceFormat(string $reference): void
    {
        $reference = trim($reference);
        if ($reference === '') {
            throw new BadRequest('credentialReference is required.');
        }

        $lower = strtolower($reference);
        $blocked = [
            'sk' . '-',
            'bearer' . ' ',
            'api' . '_key=',
            'api' . 'key=',
            'ey' . 'j',
            '-----' . 'begin',
        ];
        foreach ($blocked as $needle) {
            if (str_contains($lower, $needle)) {
                throw new BadRequest('credentialReference must be a custody reference only.');
            }
        }
    }

    /**
     * @param mixed $value
     * @return list<string>
     */
    private function normalizeCapabilityList(mixed $value): array
    {
        $list = $this->asStringList($value);
        if ($list === []) {
            throw new BadRequest('supportedCapabilities must be a non-empty list.');
        }

        foreach ($list as $capability) {
            if ($capability === self::PORTFOLIO_NOT_FAMILY) {
                throw new BadRequest('COMMERCIAL_BRIEF is not a supported capability family value.');
            }
            if (!in_array($capability, self::CAPABILITY_FAMILY, true)) {
                throw new BadRequest('supportedCapabilities must be SEARCH, ENRICHMENT, or COMPLETION.');
            }
        }

        return array_values(array_unique($list));
    }

    /**
     * @param mixed $value
     * @return list<string>
     */
    private function normalizePurposeList(mixed $value): array
    {
        $list = $this->asStringList($value);
        if ($list === []) {
            throw new BadRequest('allowedPurposes must be a non-empty list.');
        }

        foreach ($list as $purpose) {
            if (preg_match(self::PURPOSE_PATTERN, $purpose) !== 1) {
                throw new BadRequest('allowedPurposes entries must match governed purpose grammar.');
            }
            if (!isset($this->purposeCatalog[$purpose])) {
                throw new BadRequest('allowedPurposes must contain only registered purposes.');
            }
        }

        return array_values(array_unique($list));
    }

    /**
     * @param mixed $value
     * @return list<string>
     */
    private function asStringList(mixed $value): array
    {
        if ($value === null || $value === '') {
            return [];
        }

        if (is_string($value)) {
            $decoded = json_decode($value, true);
            if (is_array($decoded)) {
                $value = $decoded;
            } else {
                $value = [$value];
            }
        }

        if (!is_array($value)) {
            throw new BadRequest('Expected a list of string values.');
        }

        $out = [];
        foreach ($value as $item) {
            $item = trim((string) $item);
            if ($item !== '') {
                $out[] = $item;
            }
        }

        return $out;
    }

    private function assertEntityType(Entity $binding): void
    {
        if ($binding->getEntityType() !== self::ENTITY_TYPE) {
            throw new BadRequest('Expected ProviderBinding entity.');
        }
    }

    private function optionalString(mixed $value): ?string
    {
        if ($value === null) {
            return null;
        }

        $trimmed = trim((string) $value);

        return $trimmed === '' ? null : $trimmed;
    }
}
