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
 * Routes UI-only Quote commands to the workflow core.  It never writes the
 * status field itself; QuoteTransitionService remains the sole mutator.
 */
class QuoteWorkflowActionService
{
    public const ACTION_SUBMIT_FOR_REVIEW = 'submit-for-review';
    public const ACTION_APPROVE = 'approve';
    public const ACTION_REJECT = 'reject';
    public const ACTION_SEND = 'send';
    public const ACTION_EXPIRE = 'expire';

    /** @var array<string, array{targetStatus: string, roles: list<string>}> */
    private const ACTIONS = [
        self::ACTION_SUBMIT_FOR_REVIEW => [
            'targetStatus' => QuoteTransitionService::STATUS_IN_REVIEW,
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_APPROVE => [
            'targetStatus' => QuoteTransitionService::STATUS_APPROVED,
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_REJECT => [
            'targetStatus' => QuoteTransitionService::STATUS_REJECTED,
            'roles' => ['Manager', 'Sales Manager'],
        ],
        self::ACTION_SEND => [
            'targetStatus' => QuoteTransitionService::STATUS_SENT,
            'roles' => ['Sales', 'Sales Representative', 'Sales User'],
        ],
        self::ACTION_EXPIRE => [
            'targetStatus' => QuoteTransitionService::STATUS_EXPIRED,
            'roles' => [],
        ],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private QuoteTransitionService $transitionService,
    ) {}

    /** @return array{success: true, id: string, status: string, quoteNumber: string|null} */
    public function execute(string $quoteId, string $action): array
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
        $options = $action === self::ACTION_EXPIRE ? ['adminOverride' => true] : [];
        $quote = $this->transitionService->transition($quote, $definition['targetStatus'], $options);

        return [
            'success' => true,
            'id' => (string) $quote->getId(),
            'status' => (string) $quote->get('status'),
            'quoteNumber' => ($quote->get('quoteNumber') ?: null),
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
