<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Context;

/**
 * Immutable reference to a governed source artifact (ADR-C25-005 §4).
 *
 * Carries source artifact identity, source revision, freshness information,
 * validation state, and an evidence reference for one-click source
 * navigation. This is a pass-through record: C25 MUST NOT rewrite source meaning.
 */
final class SourceArtifactReference
{
    public function __construct(
        public readonly string $entityType,
        public readonly string $entityId,
        public readonly string $layer,
        public readonly ?string $revision,
        public readonly ?string $freshnessStatus,
        public readonly ?string $validationState,
        public readonly string $evidenceReference,
        public readonly ?string $displayName = null,
    ) {}

    /** @return array<string, mixed> */
    public function toArray(): array
    {
        return [
            'entityType' => $this->entityType,
            'entityId' => $this->entityId,
            'layer' => $this->layer,
            'revision' => $this->revision,
            'freshnessStatus' => $this->freshnessStatus,
            'validationState' => $this->validationState,
            'evidenceReference' => $this->evidenceReference,
            'displayName' => $this->displayName,
        ];
    }
}
