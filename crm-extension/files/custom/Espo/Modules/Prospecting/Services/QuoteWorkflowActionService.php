<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
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
    public const ACTION_SUBMIT_FOR_REVIEW = 'submit-for-review';
    public const ACTION_APPROVE = 'approve';
    public const ACTION_REJECT_REVIEW = 'reject-review';
    public const ACTION_MARK_CUSTOMER_REJECTED = 'mark-customer-rejected';
    /** @deprecated Backward-compat alias for mark-customer-rejected. */
    public const ACTION_REJECT = 'reject';
    public const ACTION_SEND = 'send';
    public const ACTION_EXPIRE = 'expire';

    private const TYPE_QUOTE = 'quote';
    private const TYPE_APPROVAL = 'approval';

    /** @var array<string, array{type: string, targetStatus?: string, roles: list<string>}> */
    private const ACTIONS = [
        self::ACTION_SUBMIT_FOR_REVIEW => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_IN_REVIEW,
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_APPROVE => [
            'type' => self::TYPE_APPROVAL,
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_REJECT_REVIEW => [
            'type' => self::TYPE_APPROVAL,
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_MARK_CUSTOMER_REJECTED => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_REJECTED,
            'roles' => ['Sales', 'Sales Representative', 'Sales User', 'Manager', 'Sales Manager'],
        ],
        self::ACTION_REJECT => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_REJECTED,
            'roles' => ['Sales', 'Sales Representative', 'Sales User', 'Manager', 'Sales Manager'],
        ],
        self::ACTION_SEND => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_SENT,
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_EXPIRE => [
            'type' => self::TYPE_QUOTE,
            'targetStatus' => QuoteTransitionService::STATUS_EXPIRED,
            'roles' => [],
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private QuoteTransitionService $transitionService,
        private ApprovalDecisionService $decisionService,
    ) {}

    /**
     * @return array{success: true, id: string, status: string, quoteNumber: string|null}
     */
    public function execute(string $quoteId, string $action, ?string $reason = null): array
    {
        $definition = self::ACTIONS[$action] ?? null;
        if ($definition === null) {
            throw new BadRequest('Unsupported Quote workflow action.');
        }

        $quote = $this->entityManager->getEntityById('Quote', $quoteId);
        if (!$quote instanceof Entity) {
            throw new NotFound('Quote was not found.');
        }
        if (!$this->acl->checkEntityEdit($quote)) {
            throw new Forbidden();
        }

        $this->assertActionPermission($action, $definition['roles']);

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

        if ($action === self::ACTION_APPROVE) {
            $this->decisionService->approveApproval($approval, $this->user, $reason);
        } elseif ($action === self::ACTION_REJECT_REVIEW) {
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

    /** @param list<string> $allowedRoles */
    private function assertActionPermission(string $action, array $allowedRoles): void
    {
        if ($this->user->isAdmin()) {
            return;
        }
        if ($action === self::ACTION_EXPIRE) {
            throw new Forbidden('Only administrators can expire an approved Quote manually.');
        }

        $roleNames = $this->roleNames();
        if (array_intersect($allowedRoles, $roleNames) === []) {
            throw new Forbidden('Current role cannot perform this Quote workflow action.');
        }
    }

    /** @return list<string> */
    private function roleNames(): array
    {
        $names = [];
        foreach ($this->effectiveRoleIds() as $roleId) {
            $role = $this->entityManager->getEntityById('Role', $roleId);
            if ($role instanceof Entity && trim((string) $role->get('name')) !== '') {
                $names[] = (string) $role->get('name');
            }
        }

        return array_values(array_unique($names));
    }

    /** @return list<string> */
    private function effectiveRoleIds(): array
    {
        $roleIds = $this->user->getLinkMultipleIdList('roles');
        foreach ($this->user->getLinkMultipleIdList('teams') as $teamId) {
            $team = $this->entityManager->getEntityById('Team', $teamId);
            if ($team instanceof Entity) {
                $roleIds = array_merge($roleIds, $team->getLinkMultipleIdList('roles'));
            }
        }

        return array_values(array_unique($roleIds));
    }
}
