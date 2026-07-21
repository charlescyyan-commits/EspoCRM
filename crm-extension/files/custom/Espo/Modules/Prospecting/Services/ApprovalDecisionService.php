<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
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
    /** @var list<string> */
    private const MANAGER_ROLES = ['Manager', 'Sales Manager'];

    public function __construct(
        private EntityManager $entityManager,
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
        $this->assertManagerRole($actor);

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
        $this->assertManagerRole($actor);

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

    /**
     * @throws Forbidden when the actor lacks Manager / Sales Manager role and is not admin.
     */
    private function assertManagerRole(User $actor): void
    {
        if ($actor->isAdmin()) {
            return;
        }

        $roleNames = $this->effectiveRoleNames($actor);
        if (array_intersect(self::MANAGER_ROLES, $roleNames) === []) {
            throw new Forbidden(
                'Manager role required for approval decisions.'
            );
        }
    }

    /**
     * @return list<string>
     */
    private function effectiveRoleNames(User $user): array
    {
        $roleIds = $user->getLinkMultipleIdList('roles');
        foreach ($user->getLinkMultipleIdList('teams') as $teamId) {
            $team = $this->entityManager->getEntityById('Team', $teamId);
            if ($team instanceof Entity) {
                $roleIds = array_merge($roleIds, $team->getLinkMultipleIdList('roles'));
            }
        }

        $roleIds = array_values(array_unique($roleIds));

        $names = [];
        foreach ($roleIds as $roleId) {
            $role = $this->entityManager->getEntityById('Role', $roleId);
            if ($role instanceof Entity && trim((string) $role->get('name')) !== '') {
                $names[] = (string) $role->get('name');
            }
        }

        return array_values(array_unique($names));
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
