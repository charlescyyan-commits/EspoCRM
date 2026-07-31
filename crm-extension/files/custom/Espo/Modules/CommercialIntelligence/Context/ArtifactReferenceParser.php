<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Context;

/**
 * Parses governed text references ("EntityType:entityId") from source
 * artifact reference fields.
 *
 * C25 follows governed references only. There is no foreign-key coupling
 * from C25 to any source layer (ADR-C25-005 §3.6), and reference parsing
 * never reinterprets the referencing artifact.
 */
final class ArtifactReferenceParser
{
    /**
     * The complete WP1 parser boundary. Adapter allowlists repeat these
     * checks as defense in depth, but unsupported input is rejected here
     * before adapter resolution.
     *
     * @var list<string>
     */
    public const SUPPORTED_ENTITY_TYPES = [
        'AIJob',
        'AIRequestLog',
        'ResearchEvidence',
        'AIQualificationInsight',
        'HumanFeedback',
        'ProspectCandidate',
        'ProspectRun',
        'ExecutionLedger',
        'ReplyEvent',
        'OptimizationInsight',
        'PerformanceMetric',
        'FeedbackLearningObservation',
        'ReplySignal',
        'OpportunityCandidate',
        'RevenueInsight',
        'PipelineMetric',
        'Account',
        'Contact',
        'Opportunity',
    ];

    public const MIN_ENTITY_ID_LENGTH = 8;
    public const MAX_ENTITY_ID_LENGTH = 36;

    /**
     * Capture a complete reference candidate so a forbidden character cannot
     * turn a malformed ID into a valid prefix. The leading boundary also
     * prevents namespaced and path-like types from being reinterpreted.
     */
    private const CANDIDATE_PATTERN =
        '~(?<![A-Za-z0-9_./\\\\:])([A-Za-z][A-Za-z0-9]*):([^\s,;"\'<>{}\[\]()]+)~';

    private const ENTITY_ID_PATTERN = '~\A[A-Za-z0-9]+\z~D';

    /**
     * @param mixed ...$values Raw reference field values (strings or null).
     * @return list<array{entityType: string, entityId: string}>
     */
    public static function parse(mixed ...$values): array
    {
        $found = [];

        foreach ($values as $value) {
            if (!is_string($value) || $value === '') {
                continue;
            }

            $matchCount = preg_match_all(
                self::CANDIDATE_PATTERN,
                $value,
                $matches,
                PREG_SET_ORDER
            );
            if ($matchCount === false || $matchCount === 0) {
                continue;
            }

            foreach ($matches as $match) {
                $entityType = $match[1];
                $entityId = $match[2];

                if (
                    !in_array($entityType, self::SUPPORTED_ENTITY_TYPES, true)
                    || !self::isValidEntityId($entityId)
                ) {
                    continue;
                }

                $key = $entityType . ':' . $entityId;
                $found[$key] = [
                    'entityType' => $entityType,
                    'entityId' => $entityId,
                ];
            }
        }

        return array_values($found);
    }

    private static function isValidEntityId(string $entityId): bool
    {
        $length = strlen($entityId);

        return $length >= self::MIN_ENTITY_ID_LENGTH
            && $length <= self::MAX_ENTITY_ID_LENGTH
            && preg_match(self::ENTITY_ID_PATTERN, $entityId) === 1;
    }
}
