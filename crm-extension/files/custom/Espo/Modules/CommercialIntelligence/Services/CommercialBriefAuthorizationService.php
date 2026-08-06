<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Utils\Log;
use Espo\Core\Utils\Metadata;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * C25-scoped action authorization for CommercialBrief (Plan §11 / §20.4).
 *
 * Resolves brief.* action keys via app.commercialBriefWorkflow metadata.
 * Does not mutate records, invoke generation, or write audit events.
 * Prospecting WorkflowAuthorizationService is pattern precedent only and is
 * not modified.
 */
final class CommercialBriefAuthorizationService
{
    public const ACTION_GENERATE = 'brief.generate';
    public const ACTION_REGENERATE = 'brief.regenerate';
    public const ACTION_REVIEW = 'brief.review';
    public const ACTION_ACCEPT = 'brief.accept';
    public const ACTION_DISMISS = 'brief.dismiss';
    public const ACTION_INVALIDATE = 'brief.invalidate';
    public const ACTION_ARCHIVE = 'brief.archive';
    public const ACTION_DELETE = 'brief.delete';

    /** @var list<string> */
    private const ACTIONS = [
        self::ACTION_GENERATE,
        self::ACTION_REGENERATE,
        self::ACTION_REVIEW,
        self::ACTION_ACCEPT,
        self::ACTION_DISMISS,
        self::ACTION_INVALIDATE,
        self::ACTION_ARCHIVE,
        self::ACTION_DELETE,
    ];

    /** @var array<string, string> */
    private const ACTION_ALIASES = [
        'generate' => self::ACTION_GENERATE,
        'regenerate' => self::ACTION_REGENERATE,
        'review' => self::ACTION_REVIEW,
        'accept' => self::ACTION_ACCEPT,
        'dismiss' => self::ACTION_DISMISS,
        'invalidate' => self::ACTION_INVALIDATE,
        'archive' => self::ACTION_ARCHIVE,
        'delete' => self::ACTION_DELETE,
    ];

    /** @var list<string> */
    private const CREATE_ACTIONS = [
        self::ACTION_GENERATE,
    ];

    /** @var array<string, array{roleIds: list<string>, roleNames: list<string>}>|null */
    private ?array $actionRoleBindings = null;

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private Metadata $metadata,
        private Log $log,
    ) {}

    /**
     * Authorizes a brief.* action. Generate does not require an existing brief
     * record; all other actions require entity read ACL.
     *
     * @return string One of the ACTION_* stable identifiers.
     */
    public function authorizeBriefAction(
        User $actor,
        string $action,
        ?Entity $brief = null,
    ): string {
        if ($actor->isPortal()) {
            throw new Forbidden(
                'CommercialBrief actions are internal-only; portal access is denied.'
            );
        }

        $action = $this->resolveAction($action);

        if (!in_array($action, self::CREATE_ACTIONS, true)) {
            if (
                !$brief instanceof Entity
                || $brief->getEntityType() !== 'CommercialBrief'
            ) {
                throw new BadRequest(
                    'CommercialBrief workflow action requires a CommercialBrief entity.'
                );
            }
            if (!$this->acl->checkEntityRead($brief)) {
                throw new Forbidden();
            }
        }

        $this->assertActionPermission($actor, $action);

        return $action;
    }

    /** @return string One of the ACTION_* stable identifiers. */
    public function resolveAction(string $action): string
    {
        $resolved = self::ACTION_ALIASES[$action] ?? $action;
        if (!in_array($resolved, self::ACTIONS, true)) {
            throw new BadRequest('Unsupported CommercialBrief workflow action.');
        }

        return $resolved;
    }

    private function assertActionPermission(User $actor, string $action): void
    {
        if ($actor->isAdmin()) {
            return;
        }

        $binding = $this->actionRoleBindings()[$action] ?? null;
        if (!is_array($binding)) {
            throw new Forbidden(
                'Current role cannot perform this CommercialBrief workflow action.'
            );
        }

        $roleIds = $this->effectiveRoleIds($actor);
        if (array_intersect($binding['roleIds'], $roleIds) !== []) {
            return;
        }

        if (
            array_intersect($binding['roleNames'], $this->effectiveRoleNames($actor))
            === []
        ) {
            throw new Forbidden(
                'Current role cannot perform this CommercialBrief workflow action.'
            );
        }
    }

    /** @return array<string, array{roleIds: list<string>, roleNames: list<string>}> */
    private function actionRoleBindings(): array
    {
        if ($this->actionRoleBindings !== null) {
            return $this->actionRoleBindings;
        }

        $policy = $this->metadata->get(['app', 'commercialBriefWorkflow']);
        if ($this->isValidActionRoleBindingPolicy($policy)) {
            /** @var array<string, array{roleIds: list<string>, roleNames: list<string>}> $bindings */
            $bindings = $policy['actionRoleBindings'];

            return $this->actionRoleBindings = $bindings;
        }

        $this->log->warning(
            'CommercialBrief workflow authorization metadata is missing or invalid; using fallback bindings.'
        );

        return $this->actionRoleBindings = $this->fallbackActionRoleBindings();
    }

    private function isValidActionRoleBindingPolicy(mixed $policy): bool
    {
        if (!is_array($policy) || ($policy['version'] ?? null) !== 1) {
            return false;
        }

        $bindings = $policy['actionRoleBindings'] ?? null;
        if (
            !is_array($bindings)
            || array_diff(array_keys($bindings), self::ACTIONS) !== []
            || array_diff(self::ACTIONS, array_keys($bindings)) !== []
        ) {
            return false;
        }

        foreach ($bindings as $binding) {
            if (
                !is_array($binding)
                || !$this->isStringList($binding['roleIds'] ?? null)
                || !$this->isStringList($binding['roleNames'] ?? null)
            ) {
                return false;
            }
        }

        return true;
    }

    private function isStringList(mixed $value): bool
    {
        if (!is_array($value)) {
            return false;
        }

        foreach ($value as $item) {
            if (!is_string($item) || trim($item) === '') {
                return false;
            }
        }

        return true;
    }

    /** @return array<string, array{roleIds: list<string>, roleNames: list<string>}> */
    private function fallbackActionRoleBindings(): array
    {
        return [
            self::ACTION_GENERATE => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Operator'],
            ],
            self::ACTION_REGENERATE => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Operator'],
            ],
            self::ACTION_REVIEW => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Reviewer'],
            ],
            self::ACTION_ACCEPT => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Reviewer'],
            ],
            self::ACTION_DISMISS => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Reviewer'],
            ],
            self::ACTION_INVALIDATE => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Reviewer'],
            ],
            self::ACTION_ARCHIVE => [
                'roleIds' => [],
                'roleNames' => ['Commercial Brief Operator'],
            ],
            self::ACTION_DELETE => [
                'roleIds' => [],
                'roleNames' => ['Governed Deletion'],
            ],
        ];
    }

    /** @return list<string> */
    private function effectiveRoleIds(User $user): array
    {
        $roleIds = $user->getLinkMultipleIdList('roles');
        foreach ($user->getLinkMultipleIdList('teams') as $teamId) {
            $team = $this->entityManager->getEntityById('Team', $teamId);
            if ($team instanceof Entity) {
                $roleIds = array_merge($roleIds, $team->getLinkMultipleIdList('roles'));
            }
        }

        return array_values(array_unique($roleIds));
    }

    /** @return list<string> */
    private function effectiveRoleNames(User $user): array
    {
        $names = [];
        foreach ($this->effectiveRoleIds($user) as $roleId) {
            $role = $this->entityManager->getEntityById('Role', $roleId);
            if ($role instanceof Entity && trim((string) $role->get('name')) !== '') {
                $names[] = (string) $role->get('name');
            }
        }

        return array_values(array_unique($names));
    }
}
