<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Controllers;

use Espo\Core\Api\Request;
use Espo\Core\Controllers\Record;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\HumanReviewDecisionService;

/**
 * HumanReviewDecisionRecord controller — human review outcomes only.
 * No persisted decision-intent store / workflow / CRM command paths.
 */
class HumanReviewDecisionRecord extends Record
{
    public function postActionCreateGenerated(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid create payload.');
        }
        /** @var array<string, mixed> $data */
        $record = $this->injectableFactory
            ->create(HumanReviewDecisionService::class)
            ->createGenerated($data);

        return (object) $record->getValueMap();
    }

    public function postActionMarkReviewed(Request $request): \stdClass
    {
        return $this->review($request, 'markReviewed');
    }

    public function postActionAccept(Request $request): \stdClass
    {
        return $this->review($request, 'accept');
    }

    public function postActionDismiss(Request $request): \stdClass
    {
        return $this->review($request, 'dismiss');
    }

    private function review(Request $request, string $method): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid review payload.');
        }
        $id = trim((string) ($data['id'] ?? ''));
        $reason = trim((string) ($data['reason'] ?? ''));
        if ($id === '') {
            throw new BadRequest('HumanReviewDecisionRecord id is required.');
        }
        /** @var HumanReviewDecisionService $service */
        $service = $this->injectableFactory->create(HumanReviewDecisionService::class);
        $record = $service->{$method}($id, $reason);

        return (object) $record->getValueMap();
    }
}
