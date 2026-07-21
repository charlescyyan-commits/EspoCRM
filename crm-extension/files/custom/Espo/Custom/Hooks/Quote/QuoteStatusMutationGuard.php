<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\Quote;

use Espo\Core\Exceptions\Forbidden;
use Espo\Core\Hook\Hook\BeforeSave;
use Espo\Modules\Prospecting\Services\QuoteTransitionService;
use Espo\Modules\Prospecting\Services\StatusMutationSaveOption;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

/**
 * Terminal persistence boundary for Quote.status.
 */
class QuoteStatusMutationGuard implements BeforeSave
{
    public static int $order = 1000;

    public function beforeSave(Entity $entity, SaveOptions $options): void
    {
        if ($entity->isNew()) {
            if ((string) $entity->get('status') === QuoteTransitionService::STATUS_DRAFT) {
                return;
            }

            throw new Forbidden('Quote status mutation must use QuoteTransitionService.');
        }

        if (!$entity->isAttributeChanged('status')) {
            return;
        }

        if ($options->get(StatusMutationSaveOption::QUOTE_STATUS_MUTATION_AUTHORIZED) === true) {
            return;
        }

        throw new Forbidden('Quote status mutation must use QuoteTransitionService.');
    }
}
