<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\Entities\User;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Captures human presentation / explanation feedback (governance signal only).
 *
 * No training loop, self-optimization, or shadow CRM fields.
 */
final class PresentationFeedbackService
{
    public const ENTITY_TYPE = 'PresentationFeedback';

    public const TYPE_PRESENTATION = 'PRESENTATION';
    public const TYPE_EXPLANATION_QUALITY = 'EXPLANATION_QUALITY';
    public const TYPE_ANNOTATION = 'ANNOTATION';

    public const SOURCE_FIXTURE = 'FIXTURE';
    public const SOURCE_STUB = 'STUB';
    public const SOURCE_DETERMINISTIC = 'DETERMINISTIC';
    public const SOURCE_HUMAN_AUTHORED = 'HUMAN_AUTHORED';

    /** @var list<string> */
    private const ALLOWED_TYPES = [
        self::TYPE_PRESENTATION,
        self::TYPE_EXPLANATION_QUALITY,
        self::TYPE_ANNOTATION,
    ];

    /** @var list<string> */
    private const ALLOWED_SOURCES = [
        self::SOURCE_FIXTURE,
        self::SOURCE_STUB,
        self::SOURCE_DETERMINISTIC,
        self::SOURCE_HUMAN_AUTHORED,
    ];

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
     *   feedbackType: string,
     *   feedbackContent: string,
     *   sourceEvidenceReference: string,
     *   advisorySource?: string,
     *   decisionSupportContextReference?: string,
     *   capabilityReference?: string,
     *   purposeReference?: string
     * } $input
     */
    public function submit(array $input): Entity
    {
        $this->assertHumanAuthor();

        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden('PresentationFeedback create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        $type = trim((string) ($input['feedbackType'] ?? ''));
        $content = trim((string) ($input['feedbackContent'] ?? ''));
        $source = trim((string) ($input['advisorySource'] ?? self::SOURCE_HUMAN_AUTHORED));
        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $capability = trim((string) (
            $input['capabilityReference']
                ?? DecisionSupportProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? DecisionSupportProvenanceValidator::PURPOSE_COMMERCIAL_DECISION_SUPPORT
        ));

        if ($name === '' || $content === '') {
            throw new BadRequest('PresentationFeedback name and feedbackContent are required.');
        }
        if (!in_array($type, self::ALLOWED_TYPES, true)) {
            throw new BadRequest(
                'PresentationFeedback feedbackType must be PRESENTATION, EXPLANATION_QUALITY, or ANNOTATION.'
            );
        }
        if (!in_array($source, self::ALLOWED_SOURCES, true)) {
            throw new BadRequest(
                'PresentationFeedback advisorySource must be FIXTURE, STUB, DETERMINISTIC, or HUMAN_AUTHORED.'
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        $contextRef = trim((string) ($input['decisionSupportContextReference'] ?? ''));

        /** @var Entity $feedback */
        $feedback = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $feedback->set([
            'name' => $name,
            'feedbackType' => $type,
            'feedbackContent' => $content,
            'decisionSupportContextReference' => $contextRef !== '' ? $contextRef : null,
            'sourceEvidenceReference' => $evidence,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
            'advisorySource' => $source,
        ]);

        $this->entityManager->saveEntity($feedback, [
            Wp4DecisionSupportSaveOption::FEEDBACK_CREATE_AUTHORIZED => true,
        ]);

        return $feedback;
    }

    private function assertHumanAuthor(): void
    {
        $type = strtolower(trim((string) $this->user->get('type')));
        if ($type === 'api' || $type === 'system') {
            throw new Forbidden(
                'PresentationFeedback requires a human; AI/system cannot submit training or optimization signals.'
            );
        }
        if (trim((string) $this->user->getId()) === '') {
            throw new Forbidden(
                'PresentationFeedback requires an authenticated human actor.'
            );
        }
    }
}
