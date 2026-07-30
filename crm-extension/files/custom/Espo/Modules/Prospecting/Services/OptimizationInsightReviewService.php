<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/** Human review lifecycle for immutable, advisory OptimizationInsight records. */
final class OptimizationInsightReviewService
{
    public const ENTITY_TYPE = 'OptimizationInsight';

    public const STATUS_GENERATED = 'GENERATED';
    public const STATUS_REVIEWED = 'REVIEWED';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_REJECTED = 'REJECTED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
    ) {
    }

    public function review(string $id, ?string $decisionNote = null): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_GENERATED,
            self::STATUS_REVIEWED,
            $decisionNote
        );
    }

    public function accept(string $id, ?string $decisionNote = null): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_ACCEPTED,
            $decisionNote
        );
    }

    public function reject(string $id, ?string $decisionNote = null): Entity
    {
        $decisionNote = $this->optionalText($decisionNote);
        if ($decisionNote === null) {
            throw new BadRequest(
                'Rejecting an OptimizationInsight requires a decisionNote.'
            );
        }

        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_REJECTED,
            $decisionNote
        );
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $insight = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$insight || $insight->isNew()) {
            throw new BadRequest('OptimizationInsight does not exist.');
        }
        if (!$this->acl->checkEntityRead($insight)) {
            throw new Forbidden();
        }

        return $insight;
    }

    private function transition(
        string $id,
        string $expectedStatus,
        string $targetStatus,
        ?string $decisionNote
    ): Entity {
        $insight = $this->read($id);
        if (!$this->acl->checkEntityEdit($insight)) {
            throw new Forbidden();
        }
        if ((string) $insight->get('status') !== $expectedStatus) {
            throw new Conflict(
                "OptimizationInsight must be {$expectedStatus} before {$targetStatus}."
            );
        }

        $insight->set([
            'status' => $targetStatus,
            'reviewedAt' => date('Y-m-d H:i:s'),
            'reviewedByReference' => $this->authenticatedReviewerReference(),
            'decisionNote' => $this->optionalText($decisionNote),
        ]);
        $this->entityManager->saveEntity($insight, [
            C23OptimizationInsightLifecycleSaveOption::LIFECYCLE_MUTATION_AUTHORIZED => true,
        ]);

        return $insight;
    }

    private function authenticatedReviewerReference(): string
    {
        $reference = $this->optionalText($this->user->getId());
        if ($reference === null) {
            throw new Forbidden(
                'OptimizationInsight review requires an authenticated user.'
            );
        }

        return $reference;
    }

    private function optionalText(mixed $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }
        $value = trim($value);

        return $value === '' ? null : $value;
    }
}
