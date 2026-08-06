<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Entities;

use Espo\Core\ORM\Entity;

/**
 * C25 WP2.1B CommercialBrief — persistent advisory commercial-intelligence artifact.
 *
 * Persistence-layer contract only (Plan §8 / Charter §5–§6). Generation,
 * review transitions, provider execution, and audit writer remain outside
 * this work package.
 */
final class CommercialBrief extends Entity
{
    public const ENTITY_TYPE = 'CommercialBrief';

    public const ADVISORY_DESIGNATION =
        'AI-generated commercial summary — for human review only. Not a forecast, commitment, or decision.';

    public const LEGAL_DESIGNATION =
        'AI-GENERATED_ADVISORY_PROJECTION_NOT_A_COMMERCIAL_DECISION';

    public const ACCEPTANCE_SCOPE_DECISION_SUPPORT_ONLY =
        'DECISION_SUPPORT_MATERIAL_ONLY';

    public const SECTION_MAX_LENGTH = 10000;

    public const TOTAL_CONTENT_MAX_LENGTH = 32000;

    public const SOURCE_EVIDENCE_MAX_SOURCES = 50;

    public const SOURCE_EVIDENCE_MAX_SERIALIZED_LENGTH = 16000;

    public const CLAIM_SOURCE_MAP_MAX_CLAIMS = 200;

    public const CLAIM_SOURCE_MAP_MAX_SOURCES_PER_CLAIM = 10;

    public const CLAIM_SOURCE_MAP_MAX_SERIALIZED_LENGTH = 32000;

    /** @var list<string> */
    public const SECTION_FIELDS = [
        'customerSituation',
        'commercialSignals',
        'riskFactors',
        'suggestedReviewPoints',
    ];

    /**
     * Nine immutable provenance fields (Charter §9.1 + Plan §8.1).
     *
     * @var list<string>
     */
    public const PROVENANCE_FIELDS = [
        'sourceAIJobId',
        'sourceAIRequestLogId',
        'provider',
        'model',
        'generationVersion',
        'promptTemplateId',
        'promptTemplateVersion',
        'capability',
        'purpose',
    ];

    /** @var list<string> */
    public const REVIEW_STATUS_VALUES = [
        'GENERATED',
        'REVIEWED',
        'ACCEPTED',
        'DISMISSED',
    ];

    /** @var list<string> */
    public const VALIDITY_DISPOSITION_VALUES = [
        'NONE',
        'INVALIDATED',
    ];

    /** @var list<string> */
    public const RETENTION_DISPOSITION_VALUES = [
        'ACTIVE',
        'ARCHIVED',
    ];
}
