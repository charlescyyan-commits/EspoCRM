<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Hooks\ProviderBinding;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\AIPlatform\Services\ProviderBindingMutationSaveOption;
use Espo\Modules\AIPlatform\Services\ProviderBindingService;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for ProviderBinding policy fields.
 *
 * Applies to every role, including admin. Does not dispatch, schedule,
 * resolve credentials, or contact an external system.
 */
final class ProviderBindingMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_AFTER_CREATE = [
        'providerId',
        'adapterType',
        'credentialReference',
    ];

    /** @var list<string> */
    private const SERVICE_OWNED_FIELDS = [
        'status',
        'enabled',
        'approvedById',
        'approvedAt',
        'provenanceReference',
        'supportedCapabilities',
        'allowedPurposes',
        'priority',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->getEntityType() !== ProviderBindingService::ENTITY_TYPE) {
            return;
        }

        $authorized = $options->get(
            ProviderBindingMutationSaveOption::PROVIDER_BINDING_MUTATION_AUTHORIZED
        ) === true;

        if ($entity->isNew()) {
            $this->assertValidCreateState($entity, $authorized);

            return;
        }

        foreach (self::IMMUTABLE_AFTER_CREATE as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    'ProviderBinding immutable fields may not change after create.'
                );
            }
        }

        if (!$this->hasChangedAttributes($entity, self::SERVICE_OWNED_FIELDS)) {
            return;
        }

        if ($authorized) {
            return;
        }

        throw new Forbidden(
            'ProviderBinding governed fields may only be written by ProviderBindingService.'
        );
    }

    private function assertValidCreateState(Entity $entity, bool $authorized): void
    {
        $status = (string) ($entity->get('status') ?: ProviderBindingService::STATUS_DRAFT);
        $enabled = (bool) $entity->get('enabled');

        if ($status !== ProviderBindingService::STATUS_DRAFT || $enabled !== false) {
            throw new Forbidden(
                'ProviderBinding creation must initialize to DRAFT with enabled=false.'
            );
        }

        foreach (['approvedById', 'approvedAt', 'provenanceReference'] as $field) {
            $value = $entity->get($field);
            if ($value !== null && $value !== '') {
                throw new Forbidden(
                    'ProviderBinding approval fields may only be written by ProviderBindingService.'
                );
            }
        }

        if (!$authorized) {
            throw new Forbidden('ProviderBinding create must use ProviderBindingService.');
        }
    }

    /**
     * @param list<string> $fields
     */
    private function hasChangedAttributes(Entity $entity, array $fields): bool
    {
        foreach ($fields as $field) {
            if ($entity->isAttributeChanged($field)) {
                return true;
            }
        }

        return false;
    }
}
