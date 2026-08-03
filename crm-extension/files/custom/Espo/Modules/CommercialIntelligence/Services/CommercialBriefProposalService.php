<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Services;

use Espo\Core\Acl;
use Espo\Core\Exceptions\BadRequest;
use Espo\Core\Exceptions\Forbidden;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;

/**
 * Creates CommercialBrief proposal artifacts (fixture / manual / stub only).
 *
 * Does not invoke providers, connectors, or job executors.
 */
final class CommercialBriefProposalService
{
    public const ENTITY_TYPE = 'CommercialBrief';
    public const STATUS_GENERATED = 'GENERATED';

    public const SOURCE_FIXTURE = 'FIXTURE';
    public const SOURCE_MANUAL = 'MANUAL';
    public const SOURCE_STUB = 'STUB';

    /** @var list<string> */
    private const ALLOWED_SOURCES = [
        self::SOURCE_FIXTURE,
        self::SOURCE_MANUAL,
        self::SOURCE_STUB,
    ];

    public function __construct(
        private EntityManager $entityManager,
        private Acl $acl,
        private BriefProvenanceValidator $provenanceValidator,
    ) {
    }

    /**
     * @param array{
     *   name: string,
     *   proposalContent: string,
     *   proposalSource: string,
     *   sourceEvidenceReference: string,
     *   generationContext: string,
     *   capabilityReference?: string,
     *   purposeReference?: string
     * } $input
     */
    public function createProposal(array $input): Entity
    {
        if (!$this->acl->check(self::ENTITY_TYPE, 'create')) {
            throw new Forbidden('CommercialBrief proposal create is forbidden.');
        }

        $name = trim((string) ($input['name'] ?? ''));
        $content = trim((string) ($input['proposalContent'] ?? ''));
        $source = trim((string) ($input['proposalSource'] ?? ''));
        $evidence = trim((string) ($input['sourceEvidenceReference'] ?? ''));
        $context = trim((string) ($input['generationContext'] ?? ''));
        $capability = trim((string) (
            $input['capabilityReference']
                ?? BriefProvenanceValidator::CAPABILITY_COMMERCIAL_BRIEF
        ));
        $purpose = trim((string) (
            $input['purposeReference']
                ?? BriefProvenanceValidator::PURPOSE_COMMERCIAL_BRIEF_GENERATION
        ));

        if ($name === '') {
            throw new BadRequest('CommercialBrief name is required.');
        }
        if ($content === '') {
            throw new BadRequest('CommercialBrief proposalContent is required.');
        }
        if (!in_array($source, self::ALLOWED_SOURCES, true)) {
            throw new BadRequest(
                'CommercialBrief proposalSource must be FIXTURE, MANUAL, or STUB.'
            );
        }

        $this->provenanceValidator->assertComplete([
            'sourceEvidenceReference' => $evidence,
            'generationContext' => $context,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
        ]);

        /** @var Entity $brief */
        $brief = $this->entityManager->getNewEntity(self::ENTITY_TYPE);
        $brief->set([
            'name' => $name,
            'reviewStatus' => self::STATUS_GENERATED,
            'proposalContent' => $content,
            'proposalSource' => $source,
            'sourceEvidenceReference' => $evidence,
            'generationContext' => $context,
            'capabilityReference' => $capability,
            'purposeReference' => $purpose,
            'transitionHistory' => '[]',
        ]);

        $this->entityManager->saveEntity($brief, [
            CommercialBriefSaveOption::PROPOSAL_CREATE_AUTHORIZED => true,
        ]);

        return $brief;
    }
}
