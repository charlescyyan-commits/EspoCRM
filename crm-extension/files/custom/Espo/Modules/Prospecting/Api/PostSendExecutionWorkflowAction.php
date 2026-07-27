<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\Prospecting\Services\SendExecutionWorkflowActionService;

/**
 * Thin operator entry point for the existing SendExecution recovery edges.
 * Status ownership remains exclusively in SendExecutionTransitionService.
 */
class PostSendExecutionWorkflowAction implements Action
{
    public function __construct(private SendExecutionWorkflowActionService $service) {}

    public function process(Request $request): Response
    {
        $executionId = trim((string) $request->getRouteParam('id'));
        $action = trim((string) $request->getRouteParam('action'));
        if ($executionId === '' || $action === '') {
            throw new BadRequest('SendExecution workflow route is incomplete.');
        }

        return ResponseComposer::json(
            $this->service->execute($executionId, $action, $this->extractReason($request->getParsedBody()))
        );
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

        $reason = trim($value);

        return $reason !== '' ? $reason : null;
    }
}
