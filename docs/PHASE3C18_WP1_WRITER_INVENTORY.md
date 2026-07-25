# Phase3C18 WP1.0 SendExecution Writer Inventory

**Mode:** READ-ONLY architecture audit (pre-implementation)  
**Date:** 2026-07-26  
**Baseline HEAD:** `6ee62e0fd2a119e6a82dd75f77cbab362d956d97`  
**ADR:** `docs/ADR_C18_SENDEXECUTION_LIFECYCLE_OWNERSHIP.md` (**Accepted**)  
**Governance marker:** `adr-c18-sendexecution-v1`

---

## 1. Executive Finding

Today there is **no** `SendExecutionTransitionService`.

All CRM-persisted `SendExecution.status` mutations found in packaged PHP live in two C14 adapter services:

1. `SendExecutionBridgeAdapterService`
2. `SendExecutionResultAdapterService`

Both write `status` via `$execution->set([...])` + `$this->entityManager->saveEntity($execution)`.

Additionally, the native Record controller (`Controllers/SendExecution.php`) exposes EspoCRM’s generic create/update API, which is a **latent** status/evidence writer path until WP1 forbids raw `status` patches.

No `sentAt` field or writer exists in the extension package yet (matches ADR A4).

---

## 2. Current Writer List — `SendExecution.status`

| # | Writer | Transitions written | Evidence (file:line) | Persist |
| --- | --- | --- | --- | --- |
| W1 | `SendExecutionBridgeAdapterService::receiveResult` | → `SENT` | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionBridgeAdapterService.php:54-59` (`'status' => 'SENT'`; `saveEntity` at L59) | Yes |
| W1 | same | → `FAILED` | `.../SendExecutionBridgeAdapterService.php:65-71` (`'status' => 'FAILED'`; `saveEntity` at L71) | Yes |
| W2 | `SendExecutionResultAdapterService::applyReadyTransition` (via `apply`) | `READY` → `SENT` | `crm-extension/files/custom/Espo/Modules/Prospecting/Services/SendExecutionResultAdapterService.php:55-60` set; `saveEntity` at L38 | Yes |
| W2 | same | `READY` → `FAILED` | `.../SendExecutionResultAdapterService.php:65-70` set; `saveEntity` at L38 | Yes |
| L1 | `Controllers/SendExecution` extends `Record` | Any status via generic API/UI update/create | `crm-extension/files/custom/Espo/Modules/Prospecting/Controllers/SendExecution.php:7-9` | Latent (platform Record CRUD) |

### Status writes **not** found

| Transition (ADR-C18) | Current CRM writer |
| --- | --- |
| `CREATED → READY` | **None** |
| `FAILED → READY` (retry re-arm) | **None** |
| `READY → CANCELLED` | **None** |
| `FAILED → CANCELLED` | **None** |
| Create with forced non-`CREATED` status | No dedicated service; possible via Record create (L1) |

### Non-writers (read / project only)

| Component | Role | Notes |
| --- | --- | --- |
| `EmailLifecycleProjectionHook` | AfterSave on SendExecution | Calls projection; does **not** mutate SendExecution (`.../Hooks/SendExecution/EmailLifecycleProjectionHook.php:18-21`) |
| `EmailLifecycleProjectionService::projectSendExecution` | Reads `status`; writes **Lead** | `.../EmailLifecycleProjectionService.php:137-145` |

---

## 3. Evidence-Field Write Inventory

| Field | Exists in entityDefs today | Current CRM writers | Evidence |
| --- | --- | --- | --- |
| `sentAt` | **No** | **None** | No matches under `crm-extension/files` |
| `sendRequestId` | Yes (required, unique) | No adapter **write**; Bridge uses as **lookup** key | Bridge `where(['sendRequestId' => $executionId])` at `SendExecutionBridgeAdapterService.php:76-78`. Create value expected via Record create / future factory |
| `providerName` | Yes | Bridge SENT path | `SendExecutionBridgeAdapterService.php:56` (`'providerName' => 'Brevo'`) |
| `providerMessageId` | Yes | Bridge SENT; Result SENT/FAILED clear | Bridge L57; Result L57 / L67 |
| `lastError` | Yes | Bridge FAILED; Result SENT clear / FAILED set | Bridge L68; Result L59 / L69 |
| `failureCategory` | Yes | Bridge FAILED; Result SENT clear / FAILED set | Bridge L67; Result L58 / L68 |
| `retryCount` | Yes | Bridge FAILED increments | `SendExecutionBridgeAdapterService.php:69` |
| `maxRetries` / `nextRetryAt` | Yes | **No** PHP service writers found | Schema reservation only |

### Adapter write-site detail

#### `SendExecutionBridgeAdapterService`

| Lines | Fields set |
| --- | --- |
| 54–58 | `status=SENT`, `providerName`, `providerMessageId` |
| 65–70 | `status=FAILED`, `failureCategory`, `lastError`, `retryCount++` |
| 59, 71 | `saveEntity($execution)` |
| Side effect 123–132 | Creates optional `EmailEvent` (not SendExecution) |

Accepts receive when current status ∈ `{CREATED, READY, FAILED}` (L26, L49–51) — broader than Result adapter’s READY-only gate.

#### `SendExecutionResultAdapterService`

| Lines | Fields set |
| --- | --- |
| 55–60 | `status=SENT`, `providerMessageId`, clear `failureCategory`/`lastError` |
| 65–70 | `status=FAILED`, clear `providerMessageId`, set `failureCategory`/`lastError` |
| 36–38 | Only when current status is `READY`; then `saveEntity` |
| — | Does **not** set `providerName` or increment `retryCount` |

---

## 4. Hidden / Adjacent Writer Scan

| Candidate | CRM SendExecution.status writer? | Classification |
| --- | --- | --- |
| Dashboard / Command Center JS | No | Read-only composition (`dashboard.js` links only) |
| Quote / Approval services | No | Different entities |
| Connector `send_execution.py` / worker / in-memory registries | No CRM ORM persist | Offline connector-domain state machines |
| Connector `crm_send_execution_bridge_adapter.py` / result adapter protocols | In-memory / protocol shaped | Not EspoCRM `saveEntity` writers |
| Provisioning scripts | ACL/nav only | No status mutations found for SendExecution records |

**Conclusion:** No additional packaged PHP CRM writers of `SendExecution.status` beyond W1/W2 (+ latent Record API L1).

---

## 5. Migration Targets (C18-WP1)

| Current site | Target under ADR-C18 |
| --- | --- |
| W1 / W2 direct `$execution->set('status', …)` | **Migrate** outcome transitions (`READY→SENT` / `READY→FAILED`, and any other authorized outcome paths) to call **`SendExecutionTransitionService`** |
| Bridge/Result adapters | Remain allowed to supply **provider trace** inputs; must **not** remain independent status state machines |
| Missing `CREATED→READY`, `FAILED→READY`, cancel paths | **Implement** only on `SendExecutionTransitionService` |
| Additive `sentAt` | **Introduce** in WP1 entityDefs; write **only** on successful `→ SENT` via transition service |
| `sendRequestId` | Keep create-time assignment; enforce **immutability** after create (no adapter rotation) |
| Record API `status` patch | **Forbid** for workflow clients (beforeSave guard / service override / field readOnly strategy — WP1 design choice) |
| Governance marker | Embed `adr-c18-sendexecution-v1` in metadata policy + contract tests |

---

## 6. Forbidden Writers After WP1

Per Accepted ADR-C18, the following must **not** write `SendExecution.status` (or transition-owned `sentAt`) after WP1 enforcement:

| Forbidden writer | Rationale |
| --- | --- |
| Direct adapter `$execution->set(['status' => …])` without transition service | Violates sole lifecycle owner |
| Command Center / dashboards / dashlets | C17 read-only queues |
| Client JS form patches of `status` / `sentAt` | Bypass authorizer + transition rules |
| Raw Record API / mass update of `status` | ADR §3.1 implementation gate |
| Connector workers writing CRM status via ad-hoc REST patches | Must go through authorized CRM transition/result contract |
| Projection hooks | Must continue to write Lead only, never SendExecution status |
| Any second “retry service” writing status outside transition service | Retry is `FAILED→READY` owned by transition service |

**Still allowed (non-status), subject to WP1 rules:**

- ACL-authorized **create** with initial `status=CREATED` and immutable `sendRequestId`
- Adapter / transition-owned writes of provider trace fields (`providerName`, `providerMessageId`, `lastError`, `failureCategory`) when invoked through the approved ownership path
- `retryCount` / `nextRetryAt` updates only as defined by transition/retry policy ownership (not dashboards)

---

## 7. WP1 Inventory Gaps (Pre-implementation)

1. **No transition service class** exists yet — all status ownership is still in adapters.
2. **Dual adapters** both write terminal SENT/FAILED with slightly different field side-effects (`providerName`, `retryCount` only on Bridge).
3. **Bridge accepts CREATED/FAILED** as receive states (L26), not only READY — WP1 must reconcile with ADR transition table.
4. **`sentAt` absent** — additive schema + sole writer required.
5. **Latent Record CRUD** can create/update status without workflow authorization until guarded.

---

## 8. Audit Method

Searched repository (packaged extension + connector + tests) for:

- `SendExecution` / `sendExecution`
- `->set('status'` / `'status' =>` / `saveEntity`
- Evidence fields: `sentAt`, `sendRequestId`, `providerMessageId`, `providerName`, `lastError`, `failureCategory`, `retryCount`

Confirmed entity baseline against  
`crm-extension/files/custom/Espo/Modules/Prospecting/Resources/metadata/entityDefs/SendExecution.json`.

No PHP, metadata, tests, artifacts, or tags were modified by this audit.
