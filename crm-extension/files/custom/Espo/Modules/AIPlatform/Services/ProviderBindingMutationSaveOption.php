<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

/**
 * Per-save authorization marker for ProviderBinding policy mutations.
 *
 * Its scope is one EntityManager save operation. It does not authorize
 * dispatch, retry, reservation, credential resolution, or provider invocation.
 */
final class ProviderBindingMutationSaveOption
{
    public const PROVIDER_BINDING_MUTATION_AUTHORIZED = 'aiplatform.providerBindingMutationAuthorized';
}
