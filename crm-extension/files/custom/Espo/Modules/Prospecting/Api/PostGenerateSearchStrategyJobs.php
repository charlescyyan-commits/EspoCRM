<?php

namespace Espo\Modules\Prospecting\Api;

use Espo\Core\Api\Action;
use Espo\Core\Api\Request;
use Espo\Core\Api\Response;
use Espo\Core\Api\ResponseComposer;
use Espo\Modules\Prospecting\Services\SearchStrategyService;

class PostGenerateSearchStrategyJobs implements Action
{
    public function __construct(private SearchStrategyService $service) {}

    public function process(Request $request): Response
    {
        return ResponseComposer::json($this->service->generate($request->getParsedBody()));
    }
}
