<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/** Internal write markers for the C24 ReplySignal governance boundary. */
final class C24ReplySignalSaveOption
{
    public const REPLY_SIGNAL_CREATE_AUTHORIZED =
        'c24.replySignalCreateAuthorized';
    public const LIFECYCLE_MUTATION_AUTHORIZED =
        'c24.replySignalLifecycleMutationAuthorized';

    private function __construct()
    {
    }
}
