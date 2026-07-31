<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;

/**
 * Visibility inheritance for the C25 workspace (ADR-C25-001; WP1 plan §5).
 *
 * Primary rule: C25 visibility MUST NOT exceed source visibility. If the
 * requester cannot read a source artifact at its owning layer, the C25
 * workspace cannot display it — not in a panel, not in a list, and not
 * inside an assembled summary.
 *
 * The C25 workspace is an internal surface: no portal exposure and no
 * write ACL of any kind.
 */
final class VisibilityInheritanceService
{
    public const WORKSPACE_SCOPE = 'CommercialIntelligenceWorkspace';

    public function __construct(
        private Acl $acl,
        private User $user,
    ) {}

    /**
     * Gate the workspace surface itself: internal users with an explicit
     * role grant only. Portal users are always rejected.
     */
    public function assertWorkspaceAccess(): void
    {
        if ($this->user->isPortal()) {
            throw new Forbidden(
                'Commercial intelligence workspace is internal-only; portal access is denied.'
            );
        }
        if (!$this->acl->checkScope(self::WORKSPACE_SCOPE, 'read')) {
            throw new Forbidden(
                'Commercial intelligence workspace requires an explicit role grant.'
            );
        }
    }

    /**
     * Source-permission check for a single artifact. This is the
     * visibility-inheritance point: it is enforced during assembly,
     * before anything is rendered.
     */
    public function canReadSource(Entity $entity): bool
    {
        return $this->acl->checkEntityRead($entity);
    }
}
