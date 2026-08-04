<?php

declare(strict_types=1);

namespace Espo\Modules\CommercialIntelligence\Controllers;

use Espo\Core\Api\Request;
use Espo\Core\Controllers\Record;
use Espo\Core\Exceptions\BadRequest;
use Espo\Modules\CommercialIntelligence\Services\PresentationFeedbackService;

/**
 * PresentationFeedback controller — human feedback capture only.
 * No training / optimization runtime paths.
 */
class PresentationFeedback extends Record
{
    public function postActionSubmit(Request $request): \stdClass
    {
        $data = $request->getParsedBody();
        if (!is_array($data)) {
            throw new BadRequest('Invalid feedback payload.');
        }
        /** @var array<string, mixed> $data */
        $feedback = $this->injectableFactory
            ->create(PresentationFeedbackService::class)
            ->submit($data);

        return (object) $feedback->getValueMap();
    }
}
