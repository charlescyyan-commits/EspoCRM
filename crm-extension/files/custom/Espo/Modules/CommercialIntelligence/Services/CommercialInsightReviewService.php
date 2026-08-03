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
 * Human-governed CommercialInsight review transitions.
 *
 * AI/system cannot accept, dismiss, decide, approve, execute, or mutate lifecycle.
 */
final class CommercialInsightReviewService
{
    public const ENTITY_TYPE = 'CommercialInsight';

    public const STATUS_GENERATED = 'GENERATED';
    public const STATUS_REVIEWED = 'REVIEWED';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_DISMISSED = 'DISMISSED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private InsightProvenanceValidator $provenanceValidator,
    ) {
    }

    public function markReviewed(string $id, string $reason): Entity
    {
        return $this->transition($id, self::STATUS_GENERATED, self::STATUS_REVIEWED, $reason);
    }

    public function accept(string $id, string $reason): Entity
    {
        return $this->transition($id, self::STATUS_REVIEWED, self::STATUS_ACCEPTED, $reason);
    }

    public function dismiss(string $id, string $reason): Entity
    {
        return $this->transition($id, self::STATUS_REVIEWED, self::STATUS_DISMISSED, $reason);
    }

    private function transition(
        string $id,
        string $expected,
        string $target,
        string $reason
    ): Entity {
        $this->assertHumanReviewer();

        $id = trim($id);
        $insight = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$insight || $insight->isNew()) {
            throw new BadRequest('CommercialInsight does not exist.');
        }
        if (!$this->acl->checkEntityRead($insight)) {
            throw new Forbidden();
        }
        if ((string) $insight->get('reviewStatus') !== $expected) {
            throw new Conflict(
                "CommercialInsight must be {$expected} before {$target}."
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $insight->get('sourceEvidenceReference'),
            'capabilityReference' => $insight->get('capabilityReference'),
            'purposeReference' => $insight->get('purposeReference'),
        ]);

        $actor = trim((string) $this->user->getId());
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s');
        $history = $this->history($insight);
        $history[] = [
            'fromStatus' => $expected,
            'toStatus' => $target,
            'actorReference' => $actor,
            'actorKind' => 'HUMAN',
            'transitionedAt' => $timestamp,
            'transitionReason' => $this->requiredReason($reason),
        ];

        $insight->set([
            'reviewStatus' => $target,
            'lastTransitionBy' => $actor,
            'lastTransitionAt' => $timestamp,
            'decisionNote' => $this->requiredReason($reason),
            'transitionHistory' => json_encode(
                $history,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
        ]);

        $this->entityManager->saveEntity($insight, [
            Wp3InsightSaveOption::INSIGHT_REVIEW_TRANSITION_AUTHORIZED => true,
        ]);

        return $insight;
    }

    private function assertHumanReviewer(): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                'CommercialInsight review requires a human; AI/system cannot accept, dismiss, decide, approve, or execute.'
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden('CommercialInsight review requires an authenticated human actor.');
        }
    }

    /** @return list<array<string, mixed>> */
    private function history(Entity $insight): array
    {
        $value = $insight->get('transitionHistory');
        if ($value === null || trim((string) $value) === '') {
            return [];
        }
        if (!is_string($value)) {
            throw new Conflict('CommercialInsight transitionHistory is invalid.');
        }
        try {
            $history = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Conflict('CommercialInsight transitionHistory is invalid.');
        }
        if (!is_array($history) || !array_is_list($history)) {
            throw new Conflict('CommercialInsight transitionHistory is invalid.');
        }

        return $history;
    }

    private function requiredReason(string $reason): string
    {
        $reason = trim($reason);
        if ($reason === '') {
            throw new BadRequest('CommercialInsight transition requires a reason.');
        }

        return $reason;
    }
}
