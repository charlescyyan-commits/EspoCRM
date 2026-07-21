<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

use Espo\ORM\Entity;

interface QuoteNumberingServiceInterface
{
    public function assignQuoteNumber(Entity $quote): string;
}
