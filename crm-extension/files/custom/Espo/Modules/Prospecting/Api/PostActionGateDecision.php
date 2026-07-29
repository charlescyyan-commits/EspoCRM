<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Modules\Prospecting\Services\ActionGateService;
use Espo\ORM\EntityManager;

/**
 * Human decision endpoint for an existing ActionGate.
 *
 * This endpoint cannot start execution. All mutations are delegated to the
 * existing ActionGateService authorization boundary.
 */
final class PostActionGateDecision implements Action
{
    /** @var array<string, string> */
    private const DECISIONS = [
        'approve' => ActionGateService::DECISION_APPROVED,
        'deny' => ActionGateService::DECISION_DENIED,
        'defer' => ActionGateService::DECISION_DEFERRED,
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private ActionGateService $service
    ) {}

    public function process(Request $request): Response
    {
        $gateId = trim((string) $request->getRouteParam('id'));
        $action = trim((string) $request->getRouteParam('decision'));
        if ($gateId === '' || !array_key_exists($action, self::DECISIONS)) {
            throw new BadRequest('ActionGate decision route is invalid.');
        }

        $gate = $this->entityManager->getEntity(
            ActionGateService::ENTITY_TYPE,
            $gateId
        );
        if ($gate === null || $gate->isNew()) {
            throw new BadRequest('ActionGate does not exist.');
        }
        if (!$this->acl->checkEntityRead($gate)) {
            throw new Forbidden();
        }

        $gate = $this->service->decide(
            $gate,
            self::DECISIONS[$action],
            $this->extractReason($request->getParsedBody())
        );

        return ResponseComposer::json([
            'id' => $gate->getId(),
            'decision' => $gate->get('decision'),
            'decidedAt' => $gate->get('decidedAt'),
            'decidedById' => $gate->get('decidedById'),
        ]);
    }

    private function extractReason(mixed $body): ?string
    {
        $value = null;
        if (is_array($body)) {
            $value = $body['reason'] ?? null;
        } elseif ($body instanceof \stdClass) {
            $value = $body->reason ?? null;
        }
        if (!is_string($value)) {
            return null;
        }

        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
