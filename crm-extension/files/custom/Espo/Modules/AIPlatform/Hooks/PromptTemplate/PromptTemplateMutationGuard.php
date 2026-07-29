<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Hooks\PromptTemplate;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\AIPlatform\Services\PromptTemplateSaveOption;
use Espo\Modules\AIPlatform\Services\PromptTemplateService;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Persistence boundary for PromptTemplate lifecycle and version immutability.
 */
final class PromptTemplateMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        $expectedHash = PromptTemplateService::hashContent(
            (string) $entity->get('templateBody')
        );
        if (!hash_equals($expectedHash, (string) $entity->get('contentHash'))) {
            throw new Forbidden(
                'PromptTemplate contentHash must match templateBody.'
            );
        }

        if ($entity->isNew()) {
            $this->assertDraftCreate($entity);

            return;
        }

        PromptTemplateService::assertImmutableFieldsUnchanged($entity);
        $this->assertLifecycleMutationAuthorized($entity, $options);
        $this->assertReferenceMarkAuthorized($entity, $options);
    }

    private function assertDraftCreate(Entity $entity): void
    {
        $status = (string) ($entity->get('status') ?: PromptTemplateService::STATUS_DRAFT);
        if ($status !== PromptTemplateService::STATUS_DRAFT) {
            throw new Forbidden(
                'PromptTemplate creation must start in DRAFT.'
            );
        }
        if ((bool) $entity->get('hasBeenReferenced')) {
            throw new Forbidden(
                'A new PromptTemplate cannot already be referenced.'
            );
        }
    }

    private function assertLifecycleMutationAuthorized(
        Entity $entity,
        SaveOptions $options
    ): void {
        if (!$entity->isAttributeChanged('status')) {
            return;
        }

        $authorized = $options->get(
            PromptTemplateSaveOption::LIFECYCLE_MUTATION_AUTHORIZED
        ) === true;
        if (!$authorized) {
            throw new Forbidden(
                'PromptTemplate status mutation must use PromptTemplateService.'
            );
        }
    }

    private function assertReferenceMarkAuthorized(
        Entity $entity,
        SaveOptions $options
    ): void {
        if (!$entity->isAttributeChanged('hasBeenReferenced')) {
            return;
        }

        $authorized = $options->get(
            PromptTemplateSaveOption::REFERENCE_MARK_AUTHORIZED
        ) === true;
        if (
            !$authorized
            || (bool) $entity->getFetched('hasBeenReferenced')
            || !(bool) $entity->get('hasBeenReferenced')
        ) {
            throw new Forbidden(
                'PromptTemplate reference state must be set once by PromptTemplateService.'
            );
        }
    }
}
