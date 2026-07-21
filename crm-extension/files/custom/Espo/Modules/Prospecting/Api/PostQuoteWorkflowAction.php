<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\Prospecting\Services\QuoteWorkflowActionService;

class PostQuoteWorkflowAction implements Action
{
    public function __construct(private QuoteWorkflowActionService $service) {}

    public function process(Request $request): Response
    {
        $quoteId = trim((string) $request->getRouteParam('id'));
        $action = trim((string) $request->getRouteParam('action'));
        if ($quoteId === '' || $action === '') {
            throw new BadRequest('Quote workflow route is incomplete.');
        }

        $reason = $this->extractReason($request->getParsedBody());

        return ResponseComposer::json($this->service->execute($quoteId, $action, $reason));
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
