<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence;

use Espo\Core\Binding\Binder;
use Espo\Core\Binding\BindingProcessor;

/**
 * CommercialIntelligence module bindings.
 *
 * WP2.2 CommercialBrief wiring only — no C20/C22 expansion.
 */
final class Binding implements BindingProcessor
{
    public function process(Binder $binder): void
    {
        // CommercialBrief services resolve via constructor injection.
    }
}
