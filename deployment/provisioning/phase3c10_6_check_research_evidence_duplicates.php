<?php

declare(strict_types=1);

/*
 * Read-only pre-rebuild check for the C10.6 active ResearchEvidence identity.
 *
 * Run this inside the EspoCRM container before rebuilding metadata that adds
 * the composite unique index. It never edits or deletes historic records.
 * Exit 2 means duplicate groups need manual remediation before enabling the
 * database constraint.
 */

require '/var/www/html/bootstrap.php';

$app = new \Espo\Core\Application();
$app->setupSystemUser();
$entityManager = $app->getContainer()->get('entityManager');
$groups = [];
$skipped = [];

foreach ($entityManager->getRDBRepository('ResearchEvidence')->find() as $record) {
    $leadId = text($record->get('leadId'));
    $canonicalUrl = text($record->get('peCanonicalUrl')) ?: canonicalUrl(text($record->get('peSourceUrl')));
    $evidenceType = text($record->get('peEvidenceTypeNormalized')) ?: normalizeText(text($record->get('peEvidenceType')));
    $claimHash = text($record->get('peClaimHash')) ?: hash('sha256', normalizeText(text($record->get('peClaim'))));

    if ($leadId === '' || $canonicalUrl === '' || $evidenceType === '' || text($record->get('peClaim')) === '') {
        $skipped[] = $record->getId();
        continue;
    }

    $key = json_encode([$leadId, $canonicalUrl, $evidenceType, $claimHash], JSON_THROW_ON_ERROR);
    $groups[$key] ??= [];
    $groups[$key][] = $record->getId();
}

$duplicates = array_filter($groups, static fn (array $ids): bool => count($ids) > 1);
$report = [
    'status' => $duplicates ? 'BLOCKED_HISTORY_DUPLICATES' : 'READY_FOR_REBUILD',
    'identityColumns' => ['leadId', 'peCanonicalUrl', 'peEvidenceTypeNormalized', 'peClaimHash'],
    'duplicateGroups' => array_values($duplicates),
    'skippedRecordIds' => $skipped,
    'legacyEvidenceTypeWarning' => 'Rows without normalized identity fields are evaluated from legacy values. Historic peEvidenceType values may require manual review because pre-C10.6 writers could store claim_type there.',
    'action' => $duplicates
        ? 'Do not rebuild the C10.6 unique index until duplicate groups are manually remediated.'
        : 'No duplicate groups detected; metadata rebuild may create the C10.6 unique index.',
];

echo json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . PHP_EOL;
exit($duplicates ? 2 : 0);

function text(mixed $value): string
{
    return is_string($value) ? trim($value) : '';
}

function normalizeText(string $value): string
{
    return strtolower((string) preg_replace('/\s+/u', ' ', trim($value)));
}

function canonicalUrl(string $value): string
{
    $parts = parse_url($value);
    if ($parts === false || !isset($parts['scheme'], $parts['host'])) {
        return '';
    }
    $scheme = strtolower($parts['scheme']);
    $host = strtolower($parts['host']);
    if (!in_array($scheme, ['http', 'https'], true) || $host === '') {
        return '';
    }
    $port = $parts['port'] ?? null;
    $portPart = $port !== null && !(($scheme === 'http' && $port === 80) || ($scheme === 'https' && $port === 443))
        ? ':' . $port
        : '';
    $path = $parts['path'] ?? '/';
    $path = $path === '/' ? '/' : rtrim($path, '/');
    $pairs = [];
    foreach (explode('&', $parts['query'] ?? '') as $part) {
        if ($part === '') {
            continue;
        }
        $pair = explode('=', $part, 2);
        $pairs[] = rawurlencode(rawurldecode($pair[0])) . '=' . rawurlencode(rawurldecode($pair[1] ?? ''));
    }
    sort($pairs, SORT_STRING);

    return $scheme . '://' . $host . $portPart . $path . ($pairs ? '?' . implode('&', $pairs) : '');
}
