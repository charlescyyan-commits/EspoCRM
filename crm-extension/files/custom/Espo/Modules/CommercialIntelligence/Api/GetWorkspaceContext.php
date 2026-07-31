<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\ContextAssemblyService;
use Espo\Modules\CommercialIntelligence\Services\VisibilityInheritanceService;

/**
 * Read-only workspace assembly endpoint (GET only).
 *
 * Explicit human request → assemble → render → discard. This endpoint has
 * no sibling write routes and performs no mutation of any kind.
 */
final class GetWorkspaceContext implements Action
{
    public function __construct(
        private VisibilityInheritanceService $visibility,
        private ContextAssemblyService $assemblyService,
    ) {}

    public function process(Request $request): Response
    {
        $candidateId = trim((string) $request->getRouteParam('candidateId'));
        if ($candidateId === '') {
            throw new BadRequest('A candidate anchor id is required.');
        }

        // Workspace gate: internal users with an explicit role grant only;
        // portal users are always rejected (no portal exposure).
        $this->visibility->assertWorkspaceAccess();

        $context = $this->assemblyService->assembleForCandidate($candidateId);

        return ResponseComposer::json($context->toArray());
    }
}
