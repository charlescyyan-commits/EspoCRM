<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Human-governed CommercialBrief review transitions.
 *
 * AI/system actors cannot accept, dismiss, or override review.
 */
final class CommercialBriefReviewService
{
    public const ENTITY_TYPE = 'CommercialBrief';

    public const STATUS_GENERATED = 'GENERATED';
    public const STATUS_REVIEWED = 'REVIEWED';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_DISMISSED = 'DISMISSED';

    public const ACTION_MARK_REVIEWED = 'commercialBrief.markReviewed';
    public const ACTION_ACCEPT = 'commercialBrief.accept';
    public const ACTION_DISMISS = 'commercialBrief.dismiss';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private BriefProvenanceValidator $provenanceValidator,
    ) {
    }

    public function markReviewed(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_GENERATED,
            self::STATUS_REVIEWED,
            self::ACTION_MARK_REVIEWED,
            $reason
        );
    }

    public function accept(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_ACCEPTED,
            self::ACTION_ACCEPT,
            $reason
        );
    }

    public function dismiss(string $id, string $reason): Entity
    {
        return $this->transition(
            $id,
            self::STATUS_REVIEWED,
            self::STATUS_DISMISSED,
            self::ACTION_DISMISS,
            $reason
        );
    }

    public function read(string $id): Entity
    {
        $id = trim($id);
        $brief = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$brief || $brief->isNew()) {
            throw new BadRequest('CommercialBrief does not exist.');
        }
        if (!$this->acl->checkEntityRead($brief)) {
            throw new Forbidden();
        }

        return $brief;
    }

    private function transition(
        string $id,
        string $expectedStatus,
        string $targetStatus,
        string $action,
        string $reason
    ): Entity {
        $this->assertHumanReviewer($action);

        $brief = $this->read($id);
        if ((string) $brief->get('reviewStatus') !== $expectedStatus) {
            throw new Conflict(
                "CommercialBrief must be {$expectedStatus} before {$targetStatus}."
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $brief->get('sourceEvidenceReference'),
            'generationContext' => $brief->get('generationContext'),
            'capabilityReference' => $brief->get('capabilityReference'),
            'purposeReference' => $brief->get('purposeReference'),
        ]);

        $actor = $this->authenticatedHumanReference();
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s');
        $history = $this->transitionHistory($brief);
        $history[] = [
            'fromStatus' => $expectedStatus,
            'toStatus' => $targetStatus,
            'action' => $action,
            'actorReference' => $actor,
            'actorKind' => 'HUMAN',
            'transitionedAt' => $timestamp,
            'transitionReason' => $this->requiredReason($reason),
        ];

        $payload = [
            'reviewStatus' => $targetStatus,
            'lastTransitionBy' => $actor,
            'lastTransitionAt' => $timestamp,
            'transitionHistory' => json_encode(
                $history,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
            'decisionNote' => $this->requiredReason($reason),
        ];
        if ($targetStatus === self::STATUS_REVIEWED) {
            $payload['reviewedBy'] = $actor;
            $payload['reviewedAt'] = $timestamp;
        }
        $brief->set($payload);

        $this->entityManager->saveEntity($brief, [
            CommercialBriefSaveOption::REVIEW_TRANSITION_AUTHORIZED => true,
        ]);

        return $brief;
    }

    private function assertHumanReviewer(string $action): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                "CommercialBrief action {$action} requires a human reviewer; AI/system cannot accept, dismiss, or override review."
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden(
                "CommercialBrief action {$action} requires an authenticated human actor."
            );
        }
    }

    private function authenticatedHumanReference(): string
    {
        $reference = trim((string) $this->user->getId());
        if ($reference === '') {
            throw new Forbidden(
                'CommercialBrief transition requires an authenticated human actor.'
            );
        }

        return $reference;
    }

    /** @return list<array<string, mixed>> */
    private function transitionHistory(Entity $brief): array
    {
        $value = $brief->get('transitionHistory');
        if ($value === null || trim((string) $value) === '') {
            return [];
        }
        if (!is_string($value)) {
            throw new Conflict('CommercialBrief transitionHistory is invalid.');
        }
        try {
            $history = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Conflict('CommercialBrief transitionHistory is invalid.');
        }
        if (!is_array($history) || !array_is_list($history)) {
            throw new Conflict('CommercialBrief transitionHistory is invalid.');
        }

        return $history;
    }

    private function requiredReason(string $reason): string
    {
        $reason = trim($reason);
        if ($reason === '') {
            throw new BadRequest('CommercialBrief transition requires a reason.');
        }

        return $reason;
    }
}
