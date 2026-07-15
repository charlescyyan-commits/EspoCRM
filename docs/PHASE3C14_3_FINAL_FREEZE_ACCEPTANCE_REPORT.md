# Phase3C14.3 Final Freeze Acceptance Report

## Verdict

**FREEZE_APPROVED_WITH_RISKS**

C14.3.1A through C14.3.1D form a coherent, test-backed boundary that can be
frozen for the approved scope. The audit found no C14.3 path that lets a
Worker, Queue, Provider, or Result Adapter directly mutate `Lead`, and no
forbidden automatic retry or real-send behavior was introduced.

This is a boundary/lifecycle freeze, not a claim that the system already has a
production durable queue or a production result-ingestion service. Those
limitations, together with the pre-existing C09/C10 connector projection
writers, are recorded below rather than hidden by the freeze verdict.

## Audit Scope and Method

The audit was read-only except for this required report artifact. It made no
code, database, schema, Worker, Queue, Provider, Brevo, retry, or commit
change. Test commands used the bundled Python runtime with `-B`; no real
delivery or live Provider invocation was performed.

The workspace was already dirty before this audit: it contains the prior
C11--C14 phase artifacts and unrelated tracked changes. Therefore this audit
does not assert a clean Git baseline; it verifies the live source boundaries,
the named frozen contracts, and current regression evidence.

## 1. Frozen Architecture

### Delivery path

```text
CRM approval and execution authority
  -> SendExecution
  -> B-1 Bridge Contract
  -> connector-owned immutable Payload Snapshot
  -> B-4 explicit operator/test invocation
  -> existing C13 Queue
  -> existing C13 Worker
  -> existing C12 Provider
```

### Result and projection path

```text
Provider terminal result
  -> explicit Result Command
  -> C14.3.1C Result Adapter
  -> SendExecution-only update
  -> SendExecution after-save hook
  -> EmailLifecycleProjectionService
  -> Lead summary projection
```

| Layer | Owner | Permitted responsibility | Not permitted in C14.3 |
|---|---|---|---|
| CRM | CRM domain | Approval and `SendExecution` lifecycle source record. | Execution payload storage, Worker execution, Provider call. |
| Bridge contract | Connector contract | Safe identity, content/recipient hashes, campaign reference, terminal vocabulary. | Raw payload or credentials in the bridge request. |
| Payload snapshot | Connector | Immutable, hash-verifiable delivery content in connector-owned SQLite storage. | CRM runtime dependency or snapshot mutation. |
| Explicit invocation | Operator/test caller | Validate a named `READY` execution and submit exactly once. | Approval-triggered automatic execution or CRM state write. |
| Queue and Worker | C13 | One-item local queue/work execution and terminal local outcome. | CRM entity, Lead, EmailEvent, or ReplyEvent write. |
| Provider | C12/Brevo adapter | Send request and normalized Provider result. | CRM/lifecycle state write or retry scheduling. |
| Result command/adapter | Explicit caller + CRM result service | Validate idempotent terminal result and update `SendExecution` only. | Direct Lead/Event/Reply write or auto resend. |
| Projection | `EmailLifecycleProjectionService` | Ordered, idempotent CRM-extension Lead summary projection. | Provider, Queue, Worker, or retry action. |

## 2. State Ownership Audit

### C14.3 result path

PASS. Static source inspection confirms:

- `SendExecutionResultAdapterService` saves only `$execution` and contains no
  `Lead` lookup, `EmailEvent`, or `ReplyEvent` writer.
- The `SendExecution` after-save hook delegates to
  `EmailLifecycleProjectionService::projectSendExecution()`.
- Across `crm-extension`, all writes to `peEmailStatus`,
  `peEmailReplyStatus`, and `peLastEmailDate` occur in
  `EmailLifecycleProjectionService.php`.
- `worker_execution.py` imports only its C13 queue/work-store and C12 Provider
  contracts; it has no CRM result adapter, EspoCRM, HTTP CRM client,
  EmailEvent, or ReplyEvent dependency.
- `brevo_provider.py` has no CRM or Lead dependency.

The C14.3 result path therefore cannot bypass the projection service. A
duplicate result produces no second source update; an old `FAILED` result
after `SENT` is a `RESULT_CONFLICT`, leaving `SendExecution` and Lead
projection unchanged.

### Global ownership caveat

The strict statement “`Lead.peEmailStatus` has one writer across the entire
repository” is **not yet true**. The frozen C09/C10 connector paths
(`email_lifecycle.py`, `campaign_projection.py`, and their remote-patch
transport) remain documented, pre-existing Lead-summary writers. C14.3.1A
explicitly excluded them from the CRM-extension refactor.

This is not a C14.3 result-path bypass: no Worker, Provider, or Result Adapter
uses those writers. It is an accepted convergence risk that must be resolved
in a separately authorized C14.4/C15 ownership decision before claiming
global single-writer authority.

## 3. Frozen Contract Audit

| Contract | Audit result | Evidence |
|---|---|---|
| C10 approval/idempotency/lifecycle | PASS | Current C10 focused suite: 43 tests passed. C14.3 bridge and invocation retain explicit `READY` validation and deterministic execution idempotency; they do not map `APPROVED` to execution. |
| C11 source records and projection | PASS WITH RISKS | SendExecution remains the source updated by the result service; projection remains ordered/idempotent. The global connector-writer convergence caveat remains deferred. |
| C12 Provider contract and error classes | PASS | Current C11/C12/C13/C14 focused suite: 99 tests passed; full connector regression: 270 passed. Provider result vocabulary and adapter interfaces were unchanged. |
| C13 Queue/Worker | PASS WITH RISKS | No C14.3 source changes to Queue/Worker. The queue is deliberately in-memory/local and has no automatic retry implementation. |
| C14.2B Brevo boundary | PASS WITH RISKS | Current C14.2B dry-run/guard suite passed. Default path remains dry-run, the acceptance recipient guard is tested, and network errors remain `RETRYABLE_FAILURE -> NETWORK -> FAILED` without an automatic resend. Live egress is still an external environment issue. |
| B-1 bridge contract | PASS | Request contains hashes rather than raw recipient/content; terminal result reuses the approved safe status/error vocabulary. |
| B-3 payload boundary | PASS WITH RISKS | Snapshot is immutable and self-verifying by deterministic hash; its raw content storage requires encrypted connector-owned persistent deployment storage. |
| B-4 invocation boundary | PASS WITH RISKS | Explicit invocation checks execution, `READY`, snapshot, and idempotency before the existing C13 in-memory Queue call; failed submission does not mutate CRM state. |
| C result boundary and D hardening | PASS WITH RISKS | Deterministic `result_id`, terminal conflict protection, duplicate no-op, and network ambiguity preservation are all covered by focused tests. Runtime ingestion remains an acceptance fixture. |

## 4. Security Audit

### Credentials and authorization data

Scoped scans covered C14.3 code, tests, and reports, together with the
C14.2B guard evidence. No credential value, authorization header value, bearer
token, or real secret was found.

Two matches require classification, not remediation:

1. `brevo_provider.py` names the `BREVO_API_KEY` configuration field and passes
   its runtime value to the existing Provider HTTP boundary. Its dataclass
   field is `repr=False`; the scan found no embedded value.
2. The B-4 design report shows `api_key=CRM_API_KEY` as an identifier-only
   design placeholder, not a credential.

### Recipient and content data

The recipient-pattern scan found only synthetic `.invalid` and `.test`
addresses in unit tests. No real recipient was found in C14.3 code, tests, or
reports. Test strings such as `test-only-key` are synthetic guard fixtures,
not deployable credentials.

Payload Snapshot intentionally retains recipient, subject, and body because
the approved B-3 design requires Worker-independent execution content. It
reduces incidental disclosure by using `repr=False`, hashes recipient/content
references for cross-boundary contracts, and rejects common credential
patterns at ingress. Encryption-at-rest is intentionally a deployment
boundary: the SQLite database must reside on a connector-owned encrypted
persistent volume. The module does not embed, create, or log encryption keys.

## 5. Test Evidence

| Suite | PASS | FAIL |
|---|---:|---:|
| C14.3.1A/B-1/B-2/B-3/B-4/C/D focused tests | 47 | 0 |
| C10 frozen-contract focused suite | 43 | 0 |
| C11/C12/C13/C14 focused lifecycle and regression suite | 99 | 0 |
| C14.2B safety gates plus C11 lifecycle/schema checks | 18 | 0 |
| Full CRM extension suite | 75 | 0 |
| Full connector regression suite | 270 | 0 |

**Test execution total: 552 PASS, 0 FAIL.** The suites intentionally overlap
(for example, full connector regression includes C10/C12/C13 coverage), so
552 is an execution count, not a count of unique test cases.

Additional audit commands passed:

- `git diff --check` reported no whitespace errors in tracked changes;
- focused source scans verified CRM-extension Lead-field ownership and the
absence of C14.3 Worker/Provider CRM-write imports; and
- scoped credential and recipient scans produced only the classified safe
references above.

## 6. Remaining Risk Register

| Risk | Freeze disposition | Required follow-up |
|---|---|---|
| C13 Queue and Worker work-store are process-local/in-memory. | Accepted C14.3 scope limitation. | C14.4: design a durable queue/work-state boundary with crash recovery, without changing retry semantics by implication. |
| Result command repository/CLI is an acceptance fixture; no durable, atomic, cross-process `result_id` inbox exists. | Accepted C14.3 scope limitation. | C14.4: design explicit durable result ingestion, atomic replay protection, and audited source authority. |
| C09/C10 connector remote summary writers coexist with CRM-extension projection ownership. | Accepted only as a documented convergence exception. | C14.4/C15: decide global single-writer convergence; do not silently redirect or remove frozen writers. |
| Payload snapshot stores delivery content; encryption is deployment-provided rather than code-managed. | Accepted conditional on encrypted connector-owned persistent storage. | C15 operational readiness: verify volume encryption, access boundary, backup/retention, and key management before production use. |
| C14.2B live Brevo acceptance is blocked by the environment TLS/egress path; delivery may be ambiguous after timeout. | Not a C14.3 code defect; no retry is authorized. | C15/operator: remediate egress, repeat preflight and dry-run, then perform one separately authorized guarded live acceptance. |
| No higher-priority terminal result policy exists. | Safe current behavior: all contradictory terminal results conflict. | C14.4, only if needed: define priority, source authority, evidence, and projection effects before code. |

## Next Phase Recommendation

Proceed only with a separately approved **C14.4 durable runtime convergence
design**. It should first decide how a durable queue/work store, result inbox,
and C09/C10-to-CRM projection convergence fit the frozen contracts. It must
not add automatic retries, resend behavior, Worker CRM writes, Provider
changes, or real sending.

After that design, C15 operational readiness may validate encrypted snapshot
storage and a remediated, guarded C14.2B network environment. Production live
sending remains outside this freeze.
