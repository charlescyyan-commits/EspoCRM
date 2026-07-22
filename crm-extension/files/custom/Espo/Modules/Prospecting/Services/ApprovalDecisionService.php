<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\NotFound;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Application orchestration layer.  This is the ONLY service allowed to
 * coordinate Approval decisions with Quote state propagation.
 *
 * Domain ownership:
 *   ApprovalService       — owns Approval.status + audit fields
 *   QuoteTransitionService — owns Quote.status
 *   ApprovalDecisionService — owns cross-domain orchestration only
 */
class ApprovalDecisionService
{
    public function __construct(
        private EntityManager $entityManager,
        private WorkflowAuthorizationService $authorizationService,
        private ApprovalService $approvalService,
        private QuoteTransitionService $transitionService,
    ) {}

    /**
     * Approve a PENDING Approval and propagate the Quote to APPROVED.
     *
     * Idempotent: succeeds if Approval is already APPROVED (propagation replay).
     * Conflict: fails if Approval is REJECTED (enforced by ApprovalService).
     * Four-eyes: enforced by ApprovalService.
     */
    public function approveApproval(Entity $approval, User $actor, ?string $reason = null): Entity
    {
        $this->assertTargetTypeQuote($approval);
        $this->assertTargetExists($approval);
        $this->authorizationService->authorizeApprovalDecision(
            $actor,
            WorkflowAuthorizationService::ACTION_APPROVE,
        );

        return $this->entityManager->getTransactionManager()->run(
            function () use ($approval, $actor, $reason): Entity {
                $approval = $this->approvalService->approve($approval, $actor, $reason);
                $this->propagateToQuote($approval, QuoteTransitionService::STATUS_APPROVED);

                return $approval;
            }
        );
    }

    /**
     * Reject a PENDING Approval and return the Quote to DRAFT.
     *
     * Idempotent: succeeds if Approval is already REJECTED (propagation replay).
     * Conflict: fails if Approval is APPROVED (enforced by ApprovalService).
     */
    public function rejectApproval(Entity $approval, User $actor, string $reason): Entity
    {
        $this->assertTargetTypeQuote($approval);
        $this->assertTargetExists($approval);
        $this->authorizationService->authorizeApprovalDecision(
            $actor,
            WorkflowAuthorizationService::ACTION_REJECT_REVIEW,
        );

        return $this->entityManager->getTransactionManager()->run(
            function () use ($approval, $actor, $reason): Entity {
                $approval = $this->approvalService->reject($approval, $actor, $reason);
                $this->propagateToQuote($approval, QuoteTransitionService::STATUS_DRAFT);

                return $approval;
            }
        );
    }

    /**
     * Propagate the approval decision to the target Quote.
     *
     * Skips the transition when the Quote is already in the desired state
     * (propagation replay / idempotency), otherwise delegates to
     * QuoteTransitionService.
     */
    private function propagateToQuote(Entity $approval, string $targetStatus): void
    {
        $quote = $this->loadTargetQuote($approval);

        $currentStatus = (string) ($quote->get('status') ?: QuoteTransitionService::STATUS_DRAFT);
        if ($currentStatus === $targetStatus) {
            return;
        }

        $this->transitionService->transition($quote, $targetStatus);
    }

    private function assertTargetTypeQuote(Entity $approval): void
    {
        $targetType = (string) $approval->get('targetType');
        if ($targetType !== ApprovalService::TARGET_TYPE_QUOTE) {
            throw new BadRequest(
                'ApprovalDecisionService only supports Quote target type.'
            );
        }
    }

    private function assertTargetExists(Entity $approval): void
    {
        $targetId = (string) $approval->get('targetId');
        if ($targetId === '') {
            throw new BadRequest('Approval has no targetId.');
        }
    }

    private function loadTargetQuote(Entity $approval): Entity
    {
        $quoteId = (string) $approval->get('targetId');
        $quote = $this->entityManager->getEntityById('Quote', $quoteId);
        if (!$quote instanceof Entity) {
            throw new NotFound('Target Quote was not found.');
        }

        return $quote;
    }
}
