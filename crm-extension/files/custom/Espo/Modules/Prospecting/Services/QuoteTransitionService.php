<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

class QuoteTransitionService
{
    public const STATUS_DRAFT = 'DRAFT';
    public const STATUS_IN_REVIEW = 'IN_REVIEW';
    public const STATUS_APPROVED = 'APPROVED';
    public const STATUS_SENT = 'SENT';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_REJECTED = 'REJECTED';
    public const STATUS_EXPIRED = 'EXPIRED';

    private const VALID_TRANSITIONS = [
        self::STATUS_DRAFT => [self::STATUS_IN_REVIEW],
        self::STATUS_IN_REVIEW => [self::STATUS_APPROVED, self::STATUS_DRAFT],
        self::STATUS_APPROVED => [self::STATUS_SENT, self::STATUS_EXPIRED],
        self::STATUS_SENT => [self::STATUS_ACCEPTED, self::STATUS_REJECTED],
        self::STATUS_ACCEPTED => [],
        self::STATUS_REJECTED => [],
        self::STATUS_EXPIRED => [],
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private QuoteNumberingServiceInterface $numberingService,
        private User $user,
        private ApprovalService $approvalService,
    ) {}

    public function validateTransition(string $currentStatus, string $targetStatus): bool
    {
        $this->assertKnownStatus($currentStatus);
        $this->assertKnownStatus($targetStatus);

        return in_array($targetStatus, self::VALID_TRANSITIONS[$currentStatus], true);
    }

    /**
     * @param array{adminOverride?: bool, now?: DateTimeImmutable|string} $options
     */
    public function transition(Entity $quote, string $targetStatus, array $options = []): Entity
    {
        if (!$this->acl->checkEntityEdit($quote)) {
            throw new Forbidden();
        }

        $currentStatus = (string) ($quote->get('status') ?: self::STATUS_DRAFT);
        if (!$this->validateTransition($currentStatus, $targetStatus)) {
            throw new BadRequest("Quote transition {$currentStatus} -> {$targetStatus} is not allowed.");
        }

        if ($targetStatus === self::STATUS_EXPIRED && !$this->canExpire($quote, $options)) {
            throw new BadRequest('Quote cannot expire before validUntil unless an admin override is supplied.');
        }

        return $this->entityManager->getTransactionManager()->run(
            function () use ($quote, $currentStatus, $targetStatus): Entity {
                if ($currentStatus === self::STATUS_DRAFT && $targetStatus === self::STATUS_IN_REVIEW) {
                    $this->assignQuoteNumberBoundary($quote);
                }

                $quote->set('status', $targetStatus);
                $this->entityManager->saveEntity($quote, [
                    StatusMutationSaveOption::QUOTE_STATUS_MUTATION_AUTHORIZED => true,
                ]);
                $this->afterTransition($quote, $currentStatus, $targetStatus);

                return $quote;
            }
        );
    }

    /**
     * Side-effect hook invoked inside the transition transaction.
     *
     * Creates a PENDING Approval when a Quote is submitted for review.
     * Approval creation failure rolls back the Quote transition.
     */
    protected function afterTransition(Entity $quote, string $fromStatus, string $toStatus): void
    {
        if ($fromStatus === self::STATUS_DRAFT && $toStatus === self::STATUS_IN_REVIEW) {
            $this->approvalService->createForQuote($quote, $this->user);
        }
    }

    private function assignQuoteNumberBoundary(Entity $quote): void
    {
        if ((string) $quote->get('quoteNumber') !== '') {
            return;
        }

        $quote->set('quoteNumber', $this->numberingService->assignQuoteNumber($quote));
    }

    /**
     * @param array{adminOverride?: bool, now?: DateTimeImmutable|string} $options
     */
    private function canExpire(Entity $quote, array $options): bool
    {
        if (($options['adminOverride'] ?? false) === true) {
            return true;
        }

        $validUntil = $quote->get('validUntil');
        if (!is_string($validUntil) || trim($validUntil) === '') {
            return false;
        }

        $now = $options['now'] ?? new DateTimeImmutable();
        if (is_string($now)) {
            $now = new DateTimeImmutable($now);
        }
        if (!$now instanceof DateTimeImmutable) {
            throw new BadRequest('Invalid transition clock.');
        }

        return new DateTimeImmutable($validUntil) <= $now;
    }

    private function assertKnownStatus(string $status): void
    {
        if (!array_key_exists($status, self::VALID_TRANSITIONS)) {
            throw new BadRequest("Unknown Quote status: {$status}.");
        }
    }
}
