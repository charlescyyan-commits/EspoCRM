<?php

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Record\Service;
use Espo\ORM\Entity;

/**
 * ResearchEvidence entity service.
 *
 * Enforces the invariant that every ResearchEvidence record must be linked to
 * at least one intelligence parent: a Lead, a ProspectPool, or both.
 */
class ResearchEvidenceService extends Service
{
    /**
     * Validate that the entity has at least one parent (leadId or prospectPoolId).
     */
    protected function beforeCreate(Entity $entity, $data): void
    {
        parent::beforeCreate($entity, $data);
        $this->validateParentLink($entity);
    }

    /**
     * Validate that the entity retains at least one parent on update.
     */
    protected function beforeUpdate(Entity $entity, $data): void
    {
        parent::beforeUpdate($entity, $data);
        $this->validateParentLink($entity);
    }

    /**
     * Assert that ResearchEvidence has at least one parent reference.
     *
     * Evidence must be linked to a Lead, a ProspectPool, or both.
     * Evidence with neither parent is rejected.
     *
     * @throws BadRequest when both leadId and prospectPoolId are empty.
     */
    private function validateParentLink(Entity $entity): void
    {
        $leadId = $entity->get('leadId');
        $prospectPoolId = $entity->get('prospectPoolId');

        if (empty($leadId) && empty($prospectPoolId)) {
            throw new BadRequest(
                'ResearchEvidence must be linked to a Lead or a ProspectPool.'
            );
        }
    }
}
