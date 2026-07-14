# Phase T07 — Final Regression Baseline Freeze

**Date:** 2026-07-14  
**Baseline status:** **PASS**  
**Scope:** Test inventory, existing freeze-gate execution, and testing
documentation only. No PHP, Python, Connector contract, Evidence persistence,
ACL, or workflow logic was changed.

## Baseline command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\testing\run-freeze-gate.ps1 -PythonExecutable C:\Users\98624\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

This is the required offline admission command before C11.1 work. The wrapper
delegates to the fail-closed regression gate, which always runs the complete
required set; changed-path classification never reduces coverage.

## Freeze-gate result

| Measure | Result |
| --- | --- |
| Required suites | 7/7 PASS |
| Test invocations | 382/382 PASS |
| Failures / skips | 0 / 0 |
| Freeze-wrapper exit code | 0 |
| Gate result | `PASS` |
| Gate result artifact | `temp/test-results/regression-gate-20260714-173339-464.json` |
| Conditional suites | Browser acceptance: `NOT_IMPLEMENTED`, non-blocking |
| Optional suites | Performance: `NOT_IMPLEMENTED`; documentation review: `SKIPPED` |

The total is an invocation total. The 31 Worker tests are intentionally run in
addition to the complete Connector suite, so they overlap the Connector
inventory by design.

## Existing test inventory

| Layer | Inventory | Gate coverage |
| --- | --- | --- |
| Extension | 6 test modules: skeleton/metadata inventory, SearchStrategy foundation, Prospecting UI, U03 dashboard/menu UI, and ACL03 field visibility | 65/65 PASS |
| Connector | 37 test modules: sync contract/API, lifecycle/email/feedback, Evidence boundaries, acquisition providers/workers, C07-C10 lifecycle and evidence alignment | 270/270 PASS |
| Worker | 3 focused C02 worker/persistence/job-runner modules | 31/31 PASS |
| Static | SearchStrategy detail static validation | 2/2 PASS |
| Runtime | Offline runtime-harness safety, isolation, preview, and cleanup tests | 11/11 PASS |
| Regression baseline | Extension package build/install preflight and complete metadata JSON validation | 3/3 PASS |
| Runner integrity | Complete parseable required-suite output from `run-tests.ps1` | PASS |

### Runtime and browser boundary

`tests/runtime/test_runtime_harness.py` is an offline safety harness; it does
not contact a CRM, database, or provider. Automated browser acceptance and
live runtime execution are not implemented in the current freeze gate. Their
status is therefore `NOT_IMPLEMENTED`, not PASS. Any C11 browser/runtime
acceptance must supply separate runtime evidence.

## Regression policy

1. Run the baseline command before merging or promoting C11.1 work that
   touches extension, connector, testing, deployment, or runtime-harness paths.
2. Treat any non-zero exit code, required-suite failure, missing required
   suite, malformed runner summary, or missing JSON result as a regression.
3. Keep all seven required suites. Changed-path classification is advisory and
   must never select a reduced test set.
4. Preserve the current baseline at 382 passing invocations. A legitimate test
   count change requires a documented reason, an updated expected baseline,
   and a complete passing freeze-gate run.
5. Do not convert unimplemented browser, live-runtime, package-lifecycle, or
   performance coverage into a PASS without a real, safe suite and evidence.
6. Keep generated logs and JSON in `temp/test-results/`; they are run evidence,
   not release-source changes.

## Documentation update

`docs/testing/CORE_REGRESSION_GATE.md` now records the T07 command, current
suite counts, and the pre-C11 regression policy. No test-selection or test
logic was changed.

## Conclusion

The final offline regression baseline is established for the C11.1 start:
**7/7 required suites and 382/382 invocations pass with exit code 0**.
