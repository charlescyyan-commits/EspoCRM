<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Hooks\CommercialBrief;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\CommercialIntelligence\Entities\CommercialBrief;
use Espo\Modules\CommercialIntelligence\Services\CommercialBriefSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Enforces governed CommercialBrief review/disposition/deletion mutations.
 *
 * Field-set channels are gated by CommercialBriefSaveOption tokens (Plan §20.2).
 * Append-only audit event persistence is ADR-assigned to WP2.3.
 */
final class CommercialBriefStateGuard implements BeforeSave
{
    public static int $order = 1010;

    /** @var array<string, list<string>> */
    private const TRANSITIONS = [
        'GENERATED' => ['REVIEWED'],
        'REVIEWED' => ['ACCEPTED', 'DISMISSED'],
        'ACCEPTED' => [],
        'DISMISSED' => [],
    ];

    /** @var list<string> */
    private const STATUS_FIELDS = [
        'reviewStatus',
        'acceptanceScope',
        'outcomeReason',
    ];

    /** @var list<string> */
    private const VALIDITY_FIELDS = [
        'validityDisposition',
    ];

    /** @var list<string> */
    private const RETENTION_FIELDS = [
        'retentionDisposition',
    ];

    /** @var list<string> */
    private const DELETION_FIELDS = [
        'deleteId',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            return;
        }

        $statusChanged = $this->anyChanged($entity, self::STATUS_FIELDS);
        $validityChanged = $this->anyChanged($entity, self::VALIDITY_FIELDS);
        $retentionChanged = $this->anyChanged($entity, self::RETENTION_FIELDS);
        $deletionChanged = $this->anyChanged($entity, self::DELETION_FIELDS);

        $channelCount = (int) $statusChanged
            + (int) $validityChanged
            + (int) $retentionChanged
            + (int) $deletionChanged;

        if ($channelCount === 0) {
            return;
        }

        if ($channelCount > 1) {
            throw new Forbidden(
                'CommercialBrief governed mutations must use a single field-set channel.'
            );
        }

        if ($statusChanged) {
            $this->assertStatusMutation($entity, $options);

            return;
        }
        if ($validityChanged) {
            $this->assertValidityMutation($entity, $options);

            return;
        }
        if ($retentionChanged) {
            $this->assertRetentionMutation($entity, $options);

            return;
        }

        $this->assertDeletionMutation($entity, $options);
    }

    private function assertStatusMutation(Entity $entity, SaveOptions $options): void
    {
        if (
            $options->get(CommercialBriefSaveOption::STATUS_MUTATION_AUTHORIZED)
            !== true
        ) {
            throw new Forbidden(
                'CommercialBrief reviewStatus mutation must use STATUS_MUTATION_AUTHORIZED.'
            );
        }

        $from = (string) $entity->getFetched('reviewStatus');
        $to = (string) $entity->get('reviewStatus');
        if (!in_array($to, self::TRANSITIONS[$from] ?? [], true)) {
            throw new Forbidden(
                "CommercialBrief transition {$from} to {$to} is forbidden."
            );
        }

        if ($to === 'DISMISSED') {
            $reason = $entity->get('outcomeReason');
            if (!is_string($reason) || trim($reason) === '') {
                throw new Forbidden(
                    'CommercialBrief dismiss requires outcomeReason.'
                );
            }
        }

        if ($to === 'ACCEPTED') {
            if (
                (string) $entity->get('acceptanceScope')
                !== CommercialBrief::ACCEPTANCE_SCOPE_DECISION_SUPPORT_ONLY
            ) {
                throw new Forbidden(
                    'CommercialBrief accept requires DECISION_SUPPORT_MATERIAL_ONLY.'
                );
            }
        } else {
            $scope = $entity->get('acceptanceScope');
            if ($scope !== null && $scope !== '') {
                throw new Forbidden(
                    'CommercialBrief acceptanceScope is only valid when ACCEPTED.'
                );
            }
        }
    }

    private function assertValidityMutation(Entity $entity, SaveOptions $options): void
    {
        if (
            $options->get(CommercialBriefSaveOption::VALIDITY_DISPOSITION_AUTHORIZED)
            !== true
        ) {
            throw new Forbidden(
                'CommercialBrief validityDisposition mutation must use VALIDITY_DISPOSITION_AUTHORIZED.'
            );
        }

        $from = (string) $entity->getFetched('validityDisposition');
        $to = (string) $entity->get('validityDisposition');
        if ($from === 'NONE' && $to === 'INVALIDATED') {
            return;
        }

        throw new Forbidden(
            "CommercialBrief validityDisposition {$from} to {$to} is forbidden."
        );
    }

    private function assertRetentionMutation(Entity $entity, SaveOptions $options): void
    {
        if (
            $options->get(CommercialBriefSaveOption::RETENTION_DISPOSITION_AUTHORIZED)
            !== true
        ) {
            throw new Forbidden(
                'CommercialBrief retentionDisposition mutation must use RETENTION_DISPOSITION_AUTHORIZED.'
            );
        }

        $from = (string) $entity->getFetched('retentionDisposition');
        $to = (string) $entity->get('retentionDisposition');
        if ($from === 'ACTIVE' && $to === 'ARCHIVED') {
            return;
        }

        throw new Forbidden(
            "CommercialBrief retentionDisposition {$from} to {$to} is forbidden."
        );
    }

    private function assertDeletionMutation(Entity $entity, SaveOptions $options): void
    {
        if (
            $options->get(CommercialBriefSaveOption::DELETION_AUTHORIZED) !== true
        ) {
            throw new Forbidden(
                'CommercialBrief deleteId mutation must use DELETION_AUTHORIZED.'
            );
        }

        $deleteId = $entity->get('deleteId');
        if (!is_string($deleteId) || trim($deleteId) === '' || $deleteId === '0') {
            throw new Forbidden(
                'CommercialBrief governed deletion requires a non-empty deleteId.'
            );
        }
    }

    /** @param list<string> $fields */
    private function anyChanged(Entity $entity, array $fields): bool
    {
        foreach ($fields as $field) {
            if ($entity->isAttributeChanged($field)) {
                return true;
            }
        }

        return false;
    }
}
