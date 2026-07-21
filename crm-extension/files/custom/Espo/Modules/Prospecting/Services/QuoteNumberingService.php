<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\Core\Exceptions\BadRequest;
use Espo\ORM\Entity;
use Espo\ORM\EntityManager;
use PDO;

class QuoteNumberingService implements QuoteNumberingServiceInterface
{
    private const TABLE = 'numbering_sequence';
    private const SEQUENCE_PREFIX = 'QUOTE';
    private const NUMBER_PREFIX = 'QT';
    private const MAX_SEQUENCE_VALUE = 9999;

    public function __construct(private EntityManager $entityManager) {}

    public function generateQuoteNumber(int|string $year): string
    {
        $normalizedYear = $this->normalizeYear($year);
        $nextValue = $this->nextSequenceValue($normalizedYear);

        if ($nextValue > self::MAX_SEQUENCE_VALUE) {
            throw new BadRequest('Quote number sequence exceeded 9999 for year ' . $normalizedYear . '.');
        }

        return sprintf('%s-%s-%04d', self::NUMBER_PREFIX, $normalizedYear, $nextValue);
    }

    public function assignQuoteNumber(Entity $quote, int|string|null $year = null): string
    {
        $existing = trim((string) $quote->get('quoteNumber'));
        if ($existing !== '') {
            return $existing;
        }

        $quoteNumber = $this->generateQuoteNumber($year ?? date('Y'));
        $quote->set('quoteNumber', $quoteNumber);

        return $quoteNumber;
    }

    private function nextSequenceValue(int $year): int
    {
        $sequenceKey = $this->sequenceKey($year);
        $pdo = $this->pdo();

        $insert = $pdo->prepare(
            'INSERT IGNORE INTO ' . self::TABLE . ' (sequence_key, current_value) VALUES (:sequenceKey, 0)'
        );
        $insert->execute(['sequenceKey' => $sequenceKey]);

        $update = $pdo->prepare(
            'UPDATE ' . self::TABLE .
            ' SET current_value = LAST_INSERT_ID(current_value + 1)' .
            ' WHERE sequence_key = :sequenceKey'
        );
        $update->execute(['sequenceKey' => $sequenceKey]);

        $value = $pdo->query('SELECT LAST_INSERT_ID()')->fetchColumn();
        if (!is_numeric($value)) {
            throw new BadRequest('Quote number sequence did not return a numeric value.');
        }

        return (int) $value;
    }

    private function pdo(): PDO
    {
        return $this->entityManager->getPDO();
    }

    private function sequenceKey(int $year): string
    {
        return self::SEQUENCE_PREFIX . '-' . $year;
    }

    private function normalizeYear(int|string $year): int
    {
        $value = filter_var($year, FILTER_VALIDATE_INT);
        if ($value === false || $value < 2000 || $value > 9999) {
            throw new BadRequest('Quote number year must be a four-digit year.');
        }

        return (int) $value;
    }
}
