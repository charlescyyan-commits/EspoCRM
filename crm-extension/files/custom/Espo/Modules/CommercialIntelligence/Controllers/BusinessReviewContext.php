<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Controllers;

use Espo\Core\Api\Request;
use Espo\Core\Controllers\Record;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\BusinessReviewContextAggregationService;

/**
 * BusinessReviewContext controller — composition / close only.
 * No C24/C22 mutation paths.
 */
class BusinessReviewContext extends Record
{
    public function postActionAssemble(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid assemble payload.');
        }
        /** @var array<string, mixed> $data */
        $context = $this->injectableFactory
            ->create(BusinessReviewContextAggregationService::class)
            ->assemble($data);

        return (object) $context->getValueMap();
    }

    public function postActionClose(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid close payload.');
        }
        $id = trim((string) ($data['id'] ?? ''));
        $reason = trim((string) ($data['reason'] ?? ''));
        if ($id === '') {
            throw new BadRequest('BusinessReviewContext id is required.');
        }
        $context = $this->injectableFactory
            ->create(BusinessReviewContextAggregationService::class)
            ->close($id, $reason);

        return (object) $context->getValueMap();
    }
}
