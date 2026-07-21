<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\ORM\Entity;

interface QuoteNumberingServiceInterface
{
    public function generateQuoteNumber(int|string $year): string;

    public function assignQuoteNumber(Entity $quote, int|string|null $year = null): string;
}
