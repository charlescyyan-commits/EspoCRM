<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * Per-save authorization markers owned by PromptTemplateService.
 */
final class PromptTemplateSaveOption
{
    public const LIFECYCLE_MUTATION_AUTHORIZED =
        'aiPlatform.promptTemplateLifecycleMutationAuthorized';
    public const REFERENCE_MARK_AUTHORIZED =
        'aiPlatform.promptTemplateReferenceMarkAuthorized';
}
