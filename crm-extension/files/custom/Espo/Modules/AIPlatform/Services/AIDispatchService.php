<?php

declare(strict_types=1);

namespace Espo\Modules\AIPlatform\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * RT-WP3 Dispatch Foundation Lite orchestrator.
 *
 * Resolves Request → Purpose → Capability → ProviderBinding → Execution Boundary.
 * Stops at the references-only boundary. Does not invoke Connector, perform
 * HTTP, mutate ProviderBinding, resolve secrets, retry, reserve, or queue.
 */
final class AIDispatchService
{
    public const CLASS_NOT_AUTHORIZED = 'NOT_AUTHORIZED';
    public const CLASS_UNBOUND = 'UNBOUND';
    public const CLASS_DISABLED = 'DISABLED';
    public const CLASS_PURPOSE_NOT_REGISTERED = 'PURPOSE_NOT_REGISTERED';
    public const CLASS_CAPABILITY_MISMATCH = 'CAPABILITY_MISMATCH';
    public const CLASS_CREDENTIAL_REFERENCE_MISSING = 'CREDENTIAL_REFERENCE_MISSING';
    public const CLASS_BOUND = 'BOUND';

    /** Registry family required for CompletionCapability portfolio requests. */
    private const REGISTRY_FAMILY_COMPLETION = 'COMPLETION';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private ProviderBindingService $providerBindingService,
    ) {}

    /**
     * Accept a governed Lite dispatch request and stop at the execution boundary.
     *
     * @param array<string, mixed> $input
     * @return array{
     *   eligibility: string,
     *   boundary: AIDispatchExecutionBoundary|null,
     *   evaluationTrace: list<string>,
     *   request: array<string, mixed>
     * }
     */
    public function resolve(array $input): array
    {
        if (!$this->acl->check(ProviderBindingService::ENTITY_TYPE, 'read')) {
            return $this->outcome(
                self::CLASS_NOT_AUTHORIZED,
                null,
                ['caller_not_authorized_for_provider_binding_read'],
                null,
            );
        }

        $request = AIDispatchRequest::fromArray($input);
        $trace = ['request_accepted'];

        AIDispatchRuntimeGuardsLite::rejectInvalidCapability($request->getCapabilityReference());
        $trace[] = 'capability_validated';

        $this->assertPurposeRegistered($request->getPurposeReference());
        $trace[] = 'purpose_validated';

        $bindingReference = $request->getProviderBindingReference();
        $binding = $this->lookupProviderBinding($bindingReference);
        AIDispatchRuntimeGuardsLite::rejectMissingBinding($bindingReference, $binding instanceof Entity);
        $trace[] = 'provider_binding_looked_up';

        $this->assertBindingAllowsPurpose($binding, $request->getPurposeReference());
        $trace[] = 'purpose_allowed_on_binding';

        $eligibility = $this->providerBindingService->classifyEligibility(
            (string) $binding->get('providerId'),
            self::REGISTRY_FAMILY_COMPLETION,
            $request->getPurposeReference(),
        );
        $trace[] = 'eligibility_classified:' . $eligibility;

        if ($eligibility !== self::CLASS_BOUND) {
            return $this->outcome($eligibility, null, $trace, $request);
        }

        $boundary = $this->assembleBoundary($request, $binding);
        $trace[] = 'execution_boundary_assembled';
        $trace[] = 'stopped_before_connector_invocation';

        return $this->outcome(self::CLASS_BOUND, $boundary, $trace, $request);
    }

    private function assertPurposeRegistered(string $purpose): void
    {
        $purpose = trim($purpose);
        $catalog = $this->providerBindingService->getPurposeCatalog();

        if ($purpose === 'commercial_brief_generation' || !isset($catalog[$purpose])) {
            throw new BadRequest('Purpose is not registered for Dispatch Foundation Lite.');
        }

        // Fail closed: do not infer purpose from capability or entity type.
        $mapped = $catalog[$purpose];
        if (!in_array($mapped, AIDispatchRuntimeGuardsLite::COMPLETION_PORTFOLIO, true)) {
            throw new BadRequest('Registered purpose must map to the four-value CompletionCapability portfolio.');
        }
    }

    private function lookupProviderBinding(?string $providerBindingReference): ?Entity
    {
        if ($providerBindingReference === null || trim($providerBindingReference) === '') {
            return null;
        }

        $binding = $this->entityManager->getEntity(
            ProviderBindingService::ENTITY_TYPE,
            trim($providerBindingReference)
        );

        if (!$binding instanceof Entity) {
            return null;
        }

        if ($binding->getEntityType() !== ProviderBindingService::ENTITY_TYPE) {
            return null;
        }

        // Read/consume only — never persist or mutate ProviderBinding here.
        return $binding;
    }

    private function assertBindingAllowsPurpose(Entity $binding, string $purpose): void
    {
        $allowed = $binding->get('allowedPurposes');
        if (is_string($allowed)) {
            $decoded = json_decode($allowed, true);
            $allowed = is_array($decoded) ? $decoded : [$allowed];
        }

        if (!is_array($allowed)) {
            throw new BadRequest('ProviderBinding allowedPurposes is invalid.');
        }

        $normalized = [];
        foreach ($allowed as $item) {
            $item = trim((string) $item);
            if ($item !== '') {
                $normalized[] = $item;
            }
        }

        if (!in_array($purpose, $normalized, true)) {
            throw new BadRequest('Purpose is not allowed on the selected ProviderBinding.');
        }
    }

    private function assembleBoundary(AIDispatchRequest $request, Entity $binding): AIDispatchExecutionBoundary
    {
        $credentialReference = trim((string) ($binding->get('credentialReference') ?? ''));
        $bindingId = (string) $binding->getId();

        return new AIDispatchExecutionBoundary(
            $request->getRequestIdentity(),
            $request->getPurposeReference(),
            $request->getCapabilityReference(),
            [$bindingId],
            $credentialReference === '' ? null : $credentialReference,
            $request->getProvenanceReference(),
            null,
            null,
        );
    }

    /**
     * @param list<string> $trace
     * @return array{
     *   eligibility: string,
     *   boundary: AIDispatchExecutionBoundary|null,
     *   evaluationTrace: list<string>,
     *   request: array<string, mixed>|null
     * }
     */
    private function outcome(
        string $eligibility,
        ?AIDispatchExecutionBoundary $boundary,
        array $trace,
        ?AIDispatchRequest $request,
    ): array {
        return [
            'eligibility' => $eligibility,
            'boundary' => $boundary,
            'evaluationTrace' => $trace,
            'request' => $request?->toArray(),
        ];
    }
}
