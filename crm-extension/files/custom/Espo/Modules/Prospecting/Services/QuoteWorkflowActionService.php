<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\NotFound;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Routes UI Quote workflow commands to the appropriate domain or
 * orchestration service.  It never writes Quote.status or Approval.status
 * itself; it delegates exclusively.
 *
 * C16.3B-3: approve and reject-review actions now route through
 * ApprovalDecisionService instead of calling QuoteTransitionService
 * directly.
 */
class QuoteWorkflowActionService
{
    private const TYPE_QUOTE = 'quote';
    private const TYPE_APPROVAL = 'approval';

    /** @var array<string, array{type: string, targetStatus?: string}> */
    private const ACTIONS = [
        WorkflowAuthorizationService::ACTION_SUBMIT_FOR_REVIEW => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_IN_REVIEW,
        ],
        WorkflowAuthorizationService::ACTION_APPROVE => [
            'type' => self::TYPE_APPROVAL,
        ],
        WorkflowAuthorizationService::ACTION_REJECT_REVIEW => [
            'type' => self::TYPE_APPROVAL,
        ],
        WorkflowAuthorizationService::ACTION_MARK_CUSTOMER_REJECTED => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_REJECTED,
        ],
        WorkflowAuthorizationService::ACTION_SEND => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_SENT,
        ],
        WorkflowAuthorizationService::ACTION_EXPIRE => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_EXPIRED,
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private User $user,
        private WorkflowAuthorizationService $authorizationService,
        private QuoteTransitionService $transitionService,
        private ApprovalDecisionService $decisionService,
    ) {}

    /**
     * @return array{success: true, id: string, status: string, quoteNumber: string|null}
     */
    public function execute(string $quoteId, string $action, ?string $reason = null): array
    {
        $quote = $this->entityManager->getEntityById('Quote', $quoteId);
        if (!$quote instanceof Entity) {
            throw new NotFound('Quote was not found.');
        }

        $action = $this->authorizationService->authorizeQuoteAction($quote, $this->user, $action);
        $definition = self::ACTIONS[$action];

        if ($definition['type'] === self::TYPE_APPROVAL) {
            return $this->executeApprovalAction($quote, $action, $reason);
        }

        return $this->executeQuoteAction($quote, $definition['targetStatus']);
    }

    // ----------------------------------------------------------------
    // Approval-driven actions
    // ----------------------------------------------------------------

    /** @return array{success: true, id: string, status: string, quoteNumber: string|null} */
    private function executeApprovalAction(Entity $quote, string $action, ?string $reason): array
    {
        $approval = $this->findPendingApprovalForQuote((string) $quote->getId());
        if (!$approval instanceof Entity) {
            throw new NotFound('No PENDING Approval found for this Quote.');
        }

        if ($action === WorkflowAuthorizationService::ACTION_APPROVE) {
            $this->decisionService->approveApproval($approval, $this->user, $reason);
        } elseif ($action === WorkflowAuthorizationService::ACTION_REJECT_REVIEW) {
            $normalized = trim((string) $reason);
            if ($normalized === '') {
                throw new BadRequest('A rejection reason is required.');
            }
            $this->decisionService->rejectApproval($approval, $this->user, $normalized);
        } else {
            throw new BadRequest('Unsupported approval action.');
        }

        return $this->buildResult($quote);
    }

    // ----------------------------------------------------------------
    // Quote-level actions
    // ----------------------------------------------------------------

    /** @return array{success: true, id: string, status: string, quoteNumber: string|null} */
    private function executeQuoteAction(Entity $quote, string $targetStatus): array
    {
        $options = $targetStatus === QuoteTransitionService::STATUS_EXPIRED
            ? ['adminOverride' => true]
            : [];

        $quote = $this->transitionService->transition($quote, $targetStatus, $options);

        return $this->buildResult($quote);
    }

    // ----------------------------------------------------------------
    // Helpers
    // ----------------------------------------------------------------

    private function findPendingApprovalForQuote(string $quoteId): ?Entity
    {
        $approval = $this->entityManager
            ->getRDBRepository(ApprovalService::ENTITY_TYPE)
            ->where([
                'targetType' => ApprovalService::TARGET_TYPE_QUOTE,
                'targetId' => $quoteId,
                'status' => ApprovalService::STATUS_PENDING,
            ])
            ->findOne();

        return $approval instanceof Entity ? $approval : null;
    }

    /** @return array{success: true, id: string, status: string, quoteNumber: string|null} */
    private function buildResult(Entity $quote): array
    {
        // Reload to reflect any cross-domain propagation.
        $quote = $this->entityManager->getEntityById('Quote', (string) $quote->getId());

        return [
            'success' => true,
            'id' => (string) ($quote instanceof Entity ? $quote->getId() : ''),
            'status' => (string) ($quote instanceof Entity ? $quote->get('status') : ''),
            'quoteNumber' => ($quote instanceof Entity ? ($quote->get('quoteNumber') ?: null) : null),
        ];
    }

}
