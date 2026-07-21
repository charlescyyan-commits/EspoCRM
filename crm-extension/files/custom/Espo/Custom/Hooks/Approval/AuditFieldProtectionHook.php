<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\Approval;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\ApprovalService;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Prevents post-decision mutation of Approval audit truth outside the
 * ApprovalService decision path.
 */
class AuditFieldProtectionHook implements BeforeSave
{
    public static int $order = 5;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }

        $fetchedStatus = (string) $entity->getFetched('status');
        if (!in_array($fetchedStatus, [ApprovalService::STATUS_APPROVED, ApprovalService::STATUS_REJECTED], true)) {
            return;
        }

        foreach (ApprovalService::AUDIT_FIELDS as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden('Approval audit fields are immutable after a decision.');
            }
        }
    }
}
