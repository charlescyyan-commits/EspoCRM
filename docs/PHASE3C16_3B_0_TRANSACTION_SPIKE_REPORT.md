# Phase3C16.3B-0 — Transaction Spike Report

## 1. Environment

| Item | Observed runtime |
|---|---|
| Target | Local Docker Compose project `espocrm-test` (`D:\EspoCRM-Test`) |
| EspoCRM | Official `espocrm/espocrm:10.0.1`, container healthy |
| PHP | 8.4.23 CLI |
| Database | MariaDB 11.4, PDO driver `mysql` |
| Test entrypoint | `tests/spikes/phase3c16_3b_0_transaction_spike.php` copied only to `/tmp` inside the application container |

The spike bootstraps EspoCRM as its system user and uses the existing `EntityManager` and its `TransactionManager`. It writes only randomly named native `Task` probe records, never touches Quote, Approval, metadata, routes, ACL, or a Prospecting service. Every committed probe is removed by ID in `finally`; the runtime output verified `remainingProbeCount: 0`.

## 2. TransactionManager implementation findings

The pinned 10.0.1 runtime implementation at
`/var/www/html/application/Espo/ORM/TransactionManager.php` maintains an integer
`$level`.

| Operation | Level 0 | Nested level (>0) |
|---|---|---|
| `start()` | `PDO::beginTransaction()` then increment | `CREATE SAVEPOINT POINT_<level>` then increment |
| `commit()` | decrement then `PDO::commit()` | decrement then `RELEASE SAVEPOINT POINT_<level>` |
| `rollback()` | decrement then `PDO::rollBack()` | decrement then `ROLLBACK TO SAVEPOINT POINT_<level>` |

`run()` calls `start()`, commits on normal return, and rolls back then rethrows on any `Throwable`. This is savepoint-based nested transaction behavior, not a counter-only or independent-commit implementation.

## 3. Runtime test cases and observations

| Case | Runtime sequence | Observed database result |
|---|---|---|
| Outer commit after inner success | outer `run()` → inner `run()` → `EntityManager::saveEntity(Task)` → inner return → outer return | No exception; the Task existed after outer commit. |
| Inner failure | outer `run()` → inner `run()` → Task write → intentional exception, caught by outer callback → outer Task write → outer return | Inner Task did not persist; the outer follow-up Task did persist. The inner rollback restored nesting level 1, so the outer transaction remained usable. |
| Outer failure after inner success | outer `run()` → inner `run()` → Task write → inner return → intentional outer exception | The inner Task did not persist. Releasing the inner savepoint did not leak its write after the root rollback. |

The runtime also checked nesting levels: 1 at outer entry, 2 at inner entry, 1 after inner completion or inner rollback, and 0 after outer commit or rollback.

## 4. Decision

**NESTED_TRANSACTION_SUPPORTED**

EspoCRM 10.0.1 supports the required nested `TransactionManager->run()` scenario through database savepoints. Inner failure can be caught safely by the outer operation; outer failure rolls back prior successful inner work.

## 5. Impact on C16.3B design

Keep the planned `ApprovalDecisionService` outer transaction. Existing transactional public methods, including `ApprovalService`, can safely be called within that outer transaction without a transaction-wrapper refactor.

This spike does not authorize or implement Approval decisions, Approval propagation, Quote status synchronization, `IN_REVIEW → DRAFT`, UI, API, ACL, metadata, or workflow migrations.

## 6. Validation

Required validation after adding the spike:

1. PHP syntax lint for the spike.
2. Real EspoCRM 10.0.1 runtime execution of all three cases above.
3. Existing C16 focused tests.
4. Full extension test suite.

No production behavior was changed by this spike.
