<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Controllers;

use Espo\Core\Api\Request;
use Espo\Core\Controllers\Record;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\CommercialInsightProposalService;
use Espo\Modules\CommercialIntelligence\Services\CommercialInsightReviewService;

/**
 * CommercialInsight controller — advisory review surfaces only.
 * No connector / provider / job-executor paths.
 */
class CommercialInsight extends Record
{
    public function postActionCreateProposal(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid proposal payload.');
        }
        /** @var array<string, mixed> $data */
        $insight = $this->injectableFactory
            ->create(CommercialInsightProposalService::class)
            ->createProposal($data);

        return (object) $insight->getValueMap();
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
            throw new BadRequest('CommercialInsight id is required.');
        }
        /** @var CommercialInsightReviewService $service */
        $service = $this->injectableFactory->create(CommercialInsightReviewService::class);
        $insight = $service->{$method}($id, $reason);

        return (object) $insight->getValueMap();
    }
}
