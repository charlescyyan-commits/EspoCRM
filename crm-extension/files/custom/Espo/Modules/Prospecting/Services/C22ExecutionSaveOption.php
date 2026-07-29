<?php

declare(strict_types=1);

namespace Espo\Modules\Prospecting\Services;

/**
 * Internal write markers for the C22 execution governance boundary.
 */
final class C22ExecutionSaveOption
{
    public const ACTION_GATE_CREATE_AUTHORIZED =
        'c22.actionGateCreateAuthorized';
    public const ACTION_GATE_DECISION_AUTHORIZED =
        'c22.actionGateDecisionAuthorized';
    public const EXECUTION_LEDGER_CREATE_AUTHORIZED =
        'c22.executionLedgerCreateAuthorized';
    public const PROSPECT_RUN_STATUS_MUTATION_AUTHORIZED =
        'c22.prospectRunStatusMutationAuthorized';

    private function __construct()
    {
    }
}
