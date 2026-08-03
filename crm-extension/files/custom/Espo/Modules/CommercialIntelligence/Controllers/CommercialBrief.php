<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Controllers;

use Espo\Core\Api\Request;
use Espo\Core\Controllers\Record;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\CommercialBriefProposalService;
use Espo\Modules\CommercialIntelligence\Services\CommercialBriefReviewService;

/**
 * CommercialBrief record controller — read/review surfaces only.
 *
 * No connector, provider, or job-executor paths.
 */
class CommercialBrief extends Record
{
    public function postActionCreateProposal(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid proposal payload.');
        }

        /** @var array<string, mixed> $data */
        $brief = $this->getProposalService()->createProposal($data);

        return (object) $brief->getValueMap();
    }

    public function postActionMarkReviewed(Request $request): \stdClass
    {
        return $this->reviewAction($request, 'markReviewed');
    }

    public function postActionAccept(Request $request): \stdClass
    {
        return $this->reviewAction($request, 'accept');
    }

    public function postActionDismiss(Request $request): \stdClass
    {
        return $this->reviewAction($request, 'dismiss');
    }

    private function reviewAction(Request $request, string $method): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid review payload.');
        }
        $id = trim((string) ($data['id'] ?? ''));
        $reason = trim((string) ($data['reason'] ?? ''));
        if ($id === '') {
            throw new BadRequest('CommercialBrief id is required.');
        }

        $brief = $this->getReviewService()->{$method}($id, $reason);

        return (object) $brief->getValueMap();
    }

    private function getProposalService(): CommercialBriefProposalService
    {
        /** @var CommercialBriefProposalService $service */
        $service = $this->injectableFactory->create(CommercialBriefProposalService::class);

        return $service;
    }

    private function getReviewService(): CommercialBriefReviewService
    {
        /** @var CommercialBriefReviewService $service */
        $service = $this->injectableFactory->create(CommercialBriefReviewService::class);

        return $service;
    }
}
