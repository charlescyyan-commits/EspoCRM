<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Shared authorization policy for Quote workflow commands.
 *
 * This service resolves stable workflow action identifiers and checks the
 * existing record ACL and role context. It deliberately does not mutate a
 * Quote or Approval, open transactions, or invoke owner services.
 */
class WorkflowAuthorizationService
{
    public const ACTION_SUBMIT_FOR_REVIEW = 'quote.submitForReview';
    public const ACTION_APPROVE = 'quote.approve';
    public const ACTION_REJECT_REVIEW = 'quote.rejectReview';
    public const ACTION_SEND = 'quote.send';
    public const ACTION_MARK_CUSTOMER_REJECTED = 'quote.markCustomerRejected';
    public const ACTION_MARK_ACCEPTED = 'quote.markAccepted';
    public const ACTION_EXPIRE = 'quote.expire';

    /** @var array<string, string> */
    private const ACTION_ALIASES = [
        'submit-for-review' => self::ACTION_SUBMIT_FOR_REVIEW,
        'approve' => self::ACTION_APPROVE,
        'reject-review' => self::ACTION_REJECT_REVIEW,
        'send' => self::ACTION_SEND,
        'mark-customer-rejected' => self::ACTION_MARK_CUSTOMER_REJECTED,
        'mark-accepted' => self::ACTION_MARK_ACCEPTED,
        // Backward-compatible route action retained by the UI command service.
        'reject' => self::ACTION_MARK_CUSTOMER_REJECTED,
    ];

    /** @var array<string, array{roles: list<string>, adminOnly?: bool}> */
    private const ACTION_POLICIES = [
        self::ACTION_SUBMIT_FOR_REVIEW => [
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_APPROVE => [
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_REJECT_REVIEW => [
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_SEND => [
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_MARK_CUSTOMER_REJECTED => [
            'roles' => ['Sales', 'Sales Representative', 'Sales User', 'Manager', 'Sales Manager'],
        ],
        self::ACTION_MARK_ACCEPTED => [
            'roles' => ['Sales', 'Sales Representative', 'Sales User', 'Manager', 'Sales Manager'],
        ],
        self::ACTION_EXPIRE => [
            'roles' => [],
            'adminOnly' => true,
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    /**
     * Resolves and authorizes a UI Quote command, including its existing edit ACL.
     *
     * @return string One of the ACTION_* stable identifiers.
     */
    public function authorizeQuoteAction(Entity $quote, User $actor, string $action): string
    {
        $action = $this->resolveAction($action);
        if (!$this->acl->checkEntityEdit($quote)) {
            throw new Forbidden();
        }

        $this->assertActionPermission($actor, $action);

        return $action;
    }

    /**
     * Authorizes an Approval owner-service command without adding a new ACL
     * requirement. ApprovalDecisionService historically performed role-only
     * authorization; retaining that boundary preserves permission outcomes.
     */
    public function authorizeApprovalDecision(User $actor, string $action): void
    {
        $action = $this->resolveAction($action);
        if (!in_array($action, [self::ACTION_APPROVE, self::ACTION_REJECT_REVIEW], true)) {
            throw new BadRequest('Unsupported approval workflow action.');
        }

        $this->assertActionPermission($actor, $action);
    }

    /** @return string One of the ACTION_* stable identifiers. */
    public function resolveAction(string $action): string
    {
        $resolved = self::ACTION_ALIASES[$action] ?? $action;
        if (!isset(self::ACTION_POLICIES[$resolved])) {
            throw new BadRequest('Unsupported Quote workflow action.');
        }

        return $resolved;
    }

    private function assertActionPermission(User $actor, string $action): void
    {
        if ($actor->isAdmin()) {
            return;
        }

        $policy = self::ACTION_POLICIES[$action];
        if (($policy['adminOnly'] ?? false) === true) {
            throw new Forbidden('Only administrators can expire an approved Quote manually.');
        }

        if (array_intersect($policy['roles'], $this->effectiveRoleNames($actor)) === []) {
            throw new Forbidden('Current role cannot perform this Quote workflow action.');
        }
    }

    /** @return list<string> */
    private function effectiveRoleNames(User $user): array
    {
        $roleIds = $user->getLinkMultipleIdList('roles');
        foreach ($user->getLinkMultipleIdList('teams') as $teamId) {
            $team = $this->entityManager->getEntityById('Team', $teamId);
            if ($team instanceof Entity) {
                $roleIds = array_merge($roleIds, $team->getLinkMultipleIdList('roles'));
            }
        }

        $names = [];
        foreach (array_values(array_unique($roleIds)) as $roleId) {
            $role = $this->entityManager->getEntityById('Role', $roleId);
            if ($role instanceof Entity && trim((string) $role->get('name')) !== '') {
                $names[] = (string) $role->get('name');
            }
        }

        return array_values(array_unique($names));
    }
}
