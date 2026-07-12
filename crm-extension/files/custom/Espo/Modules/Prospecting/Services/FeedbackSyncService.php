<?php

namespace Espo\Modules\Prospecting\Services;

use DateTimeImmutable;
use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Conflict;
use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Exceptions\NotFound;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use stdClass;

class FeedbackSyncService
{
    private const FEEDBACK_TYPES = [
        'CONTACT_ATTEMPT', 'CUSTOMER_REPLY', 'INTERESTED', 'NOT_INTERESTED', 'NO_RESPONSE', 'WON', 'LOST',
        'EMAIL_INTERESTED', 'EMAIL_NOT_INTERESTED', 'EMAIL_BOUNCED', 'EMAIL_NO_RESPONSE',
    ];
    private const OUTCOMES = ['POSITIVE', 'NEGATIVE', 'NEUTRAL'];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
    ) {}

    public function sync(stdClass $body): array
    {
        $payload = $this->payload($body);
        $lead = $this->lead($payload);
        $externalFeedbackId = $payload['feedback_id'] ?? $this->derivedFeedbackId($lead, $payload);
        $feedback = $this->entityManager->getRDBRepository('SalesFeedback')
            ->where(['externalFeedbackId' => $externalFeedbackId])
            ->findOne();
        $created = $feedback === null;

        if ($created) {
            $this->assertScope('SalesFeedback', 'create');
            $feedback = $this->entityManager->getEntity('SalesFeedback');
        } else {
            if ($feedback->get('leadId') !== $lead->getId()) {
                throw new Conflict('Feedback external ID belongs to another Lead.');
            }
            if (!$this->acl->checkEntityEdit($feedback)) {
                throw new Forbidden();
            }
        }

        $feedback->set([
            'name' => 'Feedback: ' . $payload['feedback_type'] . ' - ' . ($lead->get('name') ?: $lead->getId()),
            'leadId' => $lead->getId(),
            'externalLeadId' => $lead->get('peCandidateId'),
            'externalFeedbackId' => $externalFeedbackId,
            'feedbackType' => $payload['feedback_type'],
            'outcome' => $payload['outcome'],
            'reason' => $payload['reason'] ?? null,
            'note' => $payload['note'] ?? null,
            'currentStage' => $payload['stage'] ?? null,
            'product' => $payload['product'] ?? null,
            'productResult' => $payload['product_result'] ?? null,
            'campaign' => $payload['campaign'] ?? null,
            'source' => 'CONNECTOR_SYNC',
            'feedbackAt' => $this->dateTime($payload['timestamp']),
            'assignedUserId' => $lead->get('assignedUserId'),
        ]);
        $this->entityManager->saveEntity($feedback);

        $signal = $this->entityManager->getRDBRepository('LearningSignal')
            ->where(['salesFeedbackId' => $feedback->getId()])
            ->findOne();
        if (!$signal) {
            throw new NotFound('Learning signal was not generated.');
        }

        return [
            'success' => true,
            'external_id' => $externalFeedbackId,
            'accepted' => true,
            'created' => $created,
            'feedback_id' => $feedback->getId(),
            'learning_signal_id' => $signal->getId(),
        ];
    }

    private function payload(stdClass $body): array
    {
        $payload = json_decode(json_encode($body, JSON_THROW_ON_ERROR), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($payload)) {
            throw new BadRequest('Feedback payload must be an object.');
        }
        foreach (['lead_id', 'feedback_type', 'outcome', 'timestamp'] as $field) {
            if (!is_string($payload[$field] ?? null) || trim($payload[$field]) === '') {
                throw new BadRequest("Missing feedback field: {$field}.");
            }
        }
        if (isset($payload['feedback_id']) && (!is_string($payload['feedback_id']) || trim($payload['feedback_id']) === '')) {
            throw new BadRequest('feedback_id must be a non-empty string.');
        }
        if (!in_array($payload['feedback_type'], self::FEEDBACK_TYPES, true)) {
            throw new BadRequest('Unsupported feedback_type.');
        }
        if (!in_array($payload['outcome'], self::OUTCOMES, true)) {
            throw new BadRequest('Unsupported outcome.');
        }
        foreach (['external_lead_id', 'reason', 'note', 'product', 'product_result', 'stage', 'campaign'] as $field) {
            if (isset($payload[$field]) && !is_string($payload[$field])) {
                throw new BadRequest("Feedback field {$field} must be a string.");
            }
        }
        $this->dateTime($payload['timestamp']);

        return $payload;
    }

    private function lead(array $payload): Entity
    {
        $lead = $this->entityManager->getRDBRepository('Lead')
            ->where(['id' => $payload['lead_id']])
            ->findOne();
        if (!$lead) {
            throw new NotFound('Lead was not found.');
        }
        if (!$this->acl->checkEntityRead($lead)) {
            throw new Forbidden();
        }
        if (isset($payload['external_lead_id']) && $payload['external_lead_id'] !== $lead->get('peCandidateId')) {
            throw new Conflict('external_lead_id does not match the Lead.');
        }

        return $lead;
    }

    private function derivedFeedbackId(Entity $lead, array $payload): string
    {
        return hash('sha256', implode('|', [
            $lead->getId(),
            $payload['feedback_type'],
            $payload['outcome'],
            $payload['product'] ?? '',
            $payload['stage'] ?? '',
            $payload['timestamp'],
        ]));
    }

    private function dateTime(string $value): string
    {
        return (new DateTimeImmutable($value))->format('Y-m-d H:i:s');
    }

    private function assertScope(string $scope, string $action): void
    {
        if (!$this->acl->check($scope, $action)) {
            throw new Forbidden();
        }
    }
}
