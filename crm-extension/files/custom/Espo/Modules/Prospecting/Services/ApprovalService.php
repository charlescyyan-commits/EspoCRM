<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Approval domain core.  This service is the only writer of Approval business
 * state.  It never mutates Quote.status; that remains outside this domain.
 */
class ApprovalService
{
    public const ENTITY_TYPE = 'Approval';

    public const STATUS_PENDING = 'PENDING';
    public const STATUS_APPROVED = 'APPROVED';
    public const STATUS_REJECTED = 'REJECTED';

    public const TARGET_TYPE_QUOTE = 'Quote';

    public const DECISION_APPROVED = 'APPROVED';
    public const DECISION_REJECTED = 'REJECTED';

    public const DEFAULT_APPROVAL_LEVEL = 1;

    /** @var list<string> */
    public const AUDIT_FIELDS = [
        'requestedById',
        'approverId',
        'decision',
        'decidedAt',
        'reason',
        'status',
        'targetType',
        'targetId',
        'approvalLevel',
    ];

    public function __construct(private EntityManager $entityManager) {}

    public function createForQuote(Entity $quote, User $requester): Entity
    {
        $this->assertEntityType($quote, 'Quote');

        return $this->entityManager->getTransactionManager()->run(
            function () use ($quote, $requester): Entity {
                $quoteId = (string) $quote->getId();
                if ($quoteId === '') {
                    throw new BadRequest('Quote id is required to create an Approval.');
                }

                if ($this->findPendingForQuoteForUpdate($quoteId) instanceof Entity) {
                    throw new Conflict('A PENDING Approval already exists for this Quote.');
                }

                $sequence = $this->countApprovalsForQuoteForUpdate($quoteId) + 1;
                $approval = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
                $approval->set([
                    'name' => $this->buildApprovalName($quote, $sequence),
                    'status' => self::STATUS_PENDING,
                    'approvalLevel' => self::DEFAULT_APPROVAL_LEVEL,
                    'targetType' => self::TARGET_TYPE_QUOTE,
                    'targetId' => $quoteId,
                    'quoteId' => $quoteId,
                    'requestedById' => (string) $requester->getId(),
                ]);
                $this->entityManager->saveEntity($approval);

                return $approval;
            }
        );
    }

    public function approve(Entity $approval, User $actor, ?string $reason = null): Entity
    {
        $this->assertEntityType($approval, self::ENTITY_TYPE);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($approval, $actor, $reason): Entity {
                $locked = $this->lockApproval((string) $approval->getId());
                $status = (string) $locked->get('status');

                if ($status === self::STATUS_APPROVED) {
                    return $locked;
                }
                if ($status === self::STATUS_REJECTED) {
                    throw new Conflict('A REJECTED Approval cannot be approved.');
                }
                if ($status !== self::STATUS_PENDING) {
                    throw new BadRequest('Only a PENDING Approval can be approved.');
                }

                $this->assertFourEyes($locked, $actor);

                $locked->set([
                    'status' => self::STATUS_APPROVED,
                    'decision' => self::DECISION_APPROVED,
                    'approverId' => (string) $actor->getId(),
                    'decidedAt' => date('Y-m-d H:i:s'),
                    'reason' => $this->normalizeOptionalReason($reason),
                ]);
                $this->entityManager->saveEntity($locked);

                return $locked;
            }
        );
    }

    public function reject(Entity $approval, User $actor, string $reason): Entity
    {
        $this->assertEntityType($approval, self::ENTITY_TYPE);

        return $this->entityManager->getTransactionManager()->run(
            function () use ($approval, $actor, $reason): Entity {
                $locked = $this->lockApproval((string) $approval->getId());
                $status = (string) $locked->get('status');

                if ($status === self::STATUS_REJECTED) {
                    return $locked;
                }
                if ($status === self::STATUS_APPROVED) {
                    throw new Conflict('An APPROVED Approval cannot be rejected.');
                }
                if ($status !== self::STATUS_PENDING) {
                    throw new BadRequest('Only a PENDING Approval can be rejected.');
                }

                $normalizedReason = $this->requireReason($reason);

                $locked->set([
                    'status' => self::STATUS_REJECTED,
                    'decision' => self::DECISION_REJECTED,
                    'approverId' => (string) $actor->getId(),
                    'decidedAt' => date('Y-m-d H:i:s'),
                    'reason' => $normalizedReason,
                ]);
                $this->entityManager->saveEntity($locked);

                return $locked;
            }
        );
    }

    private function lockApproval(string $approvalId): Entity
    {
        if ($approvalId === '') {
            throw new BadRequest('Approval id is required.');
        }

        $locked = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where(['id' => $approvalId])
            ->forUpdate()
            ->findOne();

        if (!$locked instanceof Entity) {
            throw new BadRequest('Approval was not found.');
        }

        return $locked;
    }

    private function findPendingForQuoteForUpdate(string $quoteId): ?Entity
    {
        $pending = $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where([
                'targetType' => self::TARGET_TYPE_QUOTE,
                'targetId' => $quoteId,
                'status' => self::STATUS_PENDING,
            ])
            ->forUpdate()
            ->findOne();

        return $pending instanceof Entity ? $pending : null;
    }

    private function countApprovalsForQuoteForUpdate(string $quoteId): int
    {
        return $this->entityManager
            ->getRDBRepository(self::ENTITY_TYPE)
            ->where([
                'targetType' => self::TARGET_TYPE_QUOTE,
                'targetId' => $quoteId,
            ])
            ->forUpdate()
            ->count();
    }

    private function buildApprovalName(Entity $quote, int $sequence): string
    {
        $quoteNumber = trim((string) $quote->get('quoteNumber'));
        if ($quoteNumber === '') {
            $quoteNumber = 'Quote';
        }

        return sprintf('%s Approval #%d', $quoteNumber, $sequence);
    }

    private function assertFourEyes(Entity $approval, User $actor): void
    {
        $requestedById = trim((string) $approval->get('requestedById'));
        $actorId = trim((string) $actor->getId());
        if ($requestedById !== '' && $actorId !== '' && $requestedById === $actorId) {
            throw new Forbidden('Four-eyes rule: the requester cannot approve their own Approval.');
        }
    }

    private function requireReason(string $reason): string
    {
        $normalized = trim($reason);
        if ($normalized === '') {
            throw new BadRequest('A rejection reason is required.');
        }

        return $normalized;
    }

    private function normalizeOptionalReason(?string $reason): ?string
    {
        if ($reason === null) {
            return null;
        }

        $normalized = trim($reason);

        return $normalized === '' ? null : $normalized;
    }

    private function assertEntityType(Entity $entity, string $expectedType): void
    {
        if ($entity->getEntityType() !== $expectedType) {
            throw new BadRequest("Expected entity type {$expectedType}.");
        }
    }
}
