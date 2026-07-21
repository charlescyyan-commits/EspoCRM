<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting;

use Espo\Core\Binding\Binder;
use Espo\Core\Binding\BindingProcessor;
use Espo\Modules\Prospecting\Services\QuoteNumberingService;
use Espo\Modules\Prospecting\Services\QuoteNumberingServiceInterface;

/**
 * Module DI bindings for Prospecting runtime services.
 */
class Binding implements BindingProcessor
{
    public function process(Binder $binder): void
    {
        $binder->bindImplementation(
            QuoteNumberingServiceInterface::class,
            QuoteNumberingService::class
        );
    }
}
