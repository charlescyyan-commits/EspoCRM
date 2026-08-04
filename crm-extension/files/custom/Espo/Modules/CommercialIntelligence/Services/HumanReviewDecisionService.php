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
 * Creates and transitions HumanReviewDecisionRecord (human review outcomes only).
 *
 * Not a persisted decision-intent store. AI/system cannot accept, dismiss, approve, or execute.
 */
final class HumanReviewDecisionService
{
    public const ENTITY_TYPE = 'HumanReviewDecisionRecord';

    public const STATUS_GENERATED = 'GENERATED';
    public const STATUS_REVIEWED = 'REVIEWED';
    public const STATUS_ACCEPTED = 'ACCEPTED';
    public const STATUS_DISMISSED = 'DISMISSED';

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private User $user,
        private DecisionSupportProvenanceValidator $provenanceValidator,
    ) {
    }

    /**
     * @param array{
     *   name: string,
     *   sourceEvidenceReference: string,
     *   decisionSupportContextReference?: string,
     *   reviewComment?: string,
     *   capabilityReference?: string,
     *   purposeReference?: string
     * } $input
     */
    public function createGenerated(array $input): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden('HumanReviewDecisionRecord create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        if ($name === '') {
            throw new BadRequest('HumanReviewDecisionRecord name is required.');
        }

        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $capability = trim((string) (
            $input['capabilityReference']
                ?? DecisionSupportProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? DecisionSupportProvenanceValidator::PURPOSE_COMMERCIAL_DECISION_SUPPORT
        ));
        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        $contextRef = trim((string) ($input['decisionSupportContextReference'] ?? ''));
        $comment = trim((string) ($input['reviewComment'] ?? ''));

        /** @var Entity $record */
        $record = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $record->set([
            'name' => $name,
            'reviewStatus' => self::STATUS_GENERATED,
            'decisionSupportContextReference' => $contextRef !== '' ? $contextRef : null,
            'reviewComment' => $comment !== '' ? $comment : null,
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
            'transitionHistory' => '[]',
        ]);

        $this->entityManager->saveEntity($record, [
            Wp4DecisionSupportSaveOption::REVIEW_CREATE_AUTHORIZED => true,
        ]);

        return $record;
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
        $record = $id === ''
            ? null
            : $this->entityManager->getEntity(self::ENTITY_TYPE, $id);
        if (!$record || $record->isNew()) {
            throw new BadRequest('HumanReviewDecisionRecord does not exist.');
        }
        if (!$this->acl->checkEntityRead($record)) {
            throw new Forbidden();
        }
        if ((string) $record->get('reviewStatus') !== $expected) {
            throw new Conflict(
                "HumanReviewDecisionRecord must be {$expected} before {$target}."
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $record->get('sourceEvidenceReference'),
            'capabilityReference' => $record->get('capabilityReference'),
            'purposeReference' => $record->get('purposeReference'),
        ]);

        $actor = trim((string) $this->user->getId());
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s');
        $history = $this->history($record);
        $history[] = [
            'fromStatus' => $expected,
            'toStatus' => $target,
            'actorReference' => $actor,
            'actorKind' => 'HUMAN',
            'transitionedAt' => $timestamp,
            'transitionReason' => $this->requiredReason($reason),
        ];

        $record->set([
            'reviewStatus' => $target,
            'lastTransitionBy' => $actor,
            'lastTransitionAt' => $timestamp,
            'reviewComment' => $this->requiredReason($reason),
            'transitionHistory' => json_encode(
                $history,
                JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE
            ),
        ]);

        $this->entityManager->saveEntity($record, [
            Wp4DecisionSupportSaveOption::REVIEW_TRANSITION_AUTHORIZED => true,
        ]);

        return $record;
    }

    private function assertHumanReviewer(): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                'HumanReviewDecisionRecord review requires a human; AI/system cannot accept, dismiss, decide, approve, or execute.'
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden(
                'HumanReviewDecisionRecord review requires an authenticated human actor.'
            );
        }
    }

    /** @return list<array<string, mixed>> */
    private function history(Entity $record): array
    {
        $value = $record->get('transitionHistory');
        if ($value === null || trim((string) $value) === '') {
            return [];
        }
        if (!is_string($value)) {
            throw new Conflict('HumanReviewDecisionRecord transitionHistory is invalid.');
        }
        try {
            $history = json_decode($value, true, 512, JSON_THROW_ON_ERROR);
        } catch (\JsonException) {
            throw new Conflict('HumanReviewDecisionRecord transitionHistory is invalid.');
        }
        if (!is_array($history) || !array_is_list($history)) {
            throw new Conflict('HumanReviewDecisionRecord transitionHistory is invalid.');
        }

        return $history;
    }

    private function requiredReason(string $reason): string
    {
        $reason = trim($reason);
        if ($reason === '') {
            throw new BadRequest('HumanReviewDecisionRecord transition requires a reason.');
        }

        return $reason;
    }
}
