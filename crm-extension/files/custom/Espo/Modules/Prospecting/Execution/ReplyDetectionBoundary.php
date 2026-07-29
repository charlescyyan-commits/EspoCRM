<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Execution;

use DateTimeImmutable;
use InvalidArgumentException;

/**
 * Minimal immutable boundary for a connector-reported reply outcome.
 */
final class ReplyDetectionBoundary
{
    public const DETECTED = 'DETECTED';
    public const NOT_DETECTED = 'NOT_DETECTED';
    public const UNKNOWN = 'UNKNOWN';

    /** @var list<string> */
    private const STATUSES = [
        self::DETECTED,
        self::NOT_DETECTED,
        self::UNKNOWN,
    ];

    public function __construct(
        private string $replyEventReference,
        private string $replyStatus,
        private DateTimeImmutable $timestamp,
    ) {
        $this->replyEventReference = trim($replyEventReference);
        if ($this->replyEventReference === '') {
            throw new InvalidArgumentException(
                'replyEventReference is required.'
            );
        }

        $this->replyStatus = trim($replyStatus);
        if (!in_array($this->replyStatus, self::STATUSES, true)) {
            throw new InvalidArgumentException(
                'Unsupported reply detection status.'
            );
        }
    }

    public function replyEventReference(): string
    {
        return $this->replyEventReference;
    }

    public function replyStatus(): string
    {
        return $this->replyStatus;
    }

    public function timestamp(): DateTimeImmutable
    {
        return $this->timestamp;
    }
}
