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
 * Protects immutable CommercialBrief content, provenance, designation, and anchor.
 *
 * Creation is generation-only via GENERATION_AUTHORIZED (no generic create path).
 */
final class CommercialBriefImmutableGuard implements BeforeSave
{
    public static int $order = 1000;

    /** @var list<string> */
    private const IMMUTABLE_AFTER_GENERATION = [
        'opportunityCandidateId',
        'reportingPeriod',
        'generatedAt',
        'generationVersion',
        'customerSituation',
        'commercialSignals',
        'riskFactors',
        'suggestedReviewPoints',
        'sourceEvidence',
        'evidenceSetHash',
        'claimSourceMap',
        'sourceAIJobId',
        'sourceAIRequestLogId',
        'provider',
        'model',
        'promptTemplateId',
        'promptTemplateVersion',
        'capability',
        'purpose',
        'advisoryDesignation',
        'legalDesignation',
        'createdAt',
        'createdById',
    ];

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if (
                $options->get(CommercialBriefSaveOption::GENERATION_AUTHORIZED)
                !== true
            ) {
                throw new Forbidden(
                    'CommercialBrief create must use GENERATION_AUTHORIZED save option.'
                );
            }
            $this->assertDesignationConstants($entity);

            return;
        }

        foreach (self::IMMUTABLE_AFTER_GENERATION as $field) {
            if ($entity->isAttributeChanged($field)) {
                throw new Forbidden(
                    "CommercialBrief field {$field} is immutable after generation."
                );
            }
        }

        if (
            $entity->isAttributeChanged('supersedesBriefId')
            && $entity->getFetched('supersedesBriefId') !== null
            && $entity->getFetched('supersedesBriefId') !== ''
        ) {
            throw new Forbidden(
                'CommercialBrief supersedesBriefId is immutable once set.'
            );
        }
    }

    private function assertDesignationConstants(Entity $entity): void
    {
        $advisory = (string) $entity->get('advisoryDesignation');
        $legal = (string) $entity->get('legalDesignation');
        if ($advisory !== CommercialBrief::ADVISORY_DESIGNATION) {
            throw new Forbidden(
                'CommercialBrief advisoryDesignation must equal the fixed advisory text.'
            );
        }
        if ($legal !== CommercialBrief::LEGAL_DESIGNATION) {
            throw new Forbidden(
                'CommercialBrief legalDesignation must equal the fixed legal constant.'
            );
        }
    }
}
