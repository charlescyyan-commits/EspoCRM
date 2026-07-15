<?php

declare(strict_types=1);

namespace Espo\Custom\Hooks\ReplyEvent;

use Espo\Core\Hook\Hook\AfterSave;
use Espo\Modules\Prospecting\Services\EmailLifecycleProjectionService;
use Espo\ORM\Entity;
use Espo\ORM\Repository\Option\SaveOptions;

class EmailLifecycleProjectionHook implements AfterSave
{
    public static int $order = 50;

    public function __construct(private EmailLifecycleProjectionService $projectionService) {}

    public function afterSave(Entity $entity, SaveOptions $options): void
    {
        $this->projectionService->projectReplyEvent($entity);
    }
}
