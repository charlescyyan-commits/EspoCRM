# Phase C14.2B.6 — Acceptance Environment Handoff Decision

## Final Verdict

**FREEZE_C14_2B_AND_PROCEED**

C14.2B is technically validated. The code path is correct and complete. The blocking factor is exclusively an environmental network restriction on the Brevo TLS path, which no code change can remedy. C14.3 should proceed without waiting for environment remediation.

---

## 1. Is C14.2B Technically Validated Despite External Network Failure?

**YES.**

The following code-path validations are confirmed by the evidence chain, independent of the network outcome:

### 1.1 Dry-Run Safety Gate

| Check | Evidence | Verdict |
|---|---|---|
| Default mode is dry-run | C14.2B.2: `--dry-run` is the default; no HTTP client constructed | PASS |
| `BREVO_ACCEPTANCE_MODE` must be exact `true` | C14.2B.3: runner correctly blocked with `BREVO_ACCEPTANCE_MODE_NOT_TRUE` when env vars absent | PASS |
| `BREVO_TEST_RECIPIENT` must be present | C14.2B.2: runner exits with `BREVO_TEST_RECIPIENT_MISSING` before HTTP | PASS |
| `BREVO_API_KEY` must be present | C14.2B.2: enforced before transport construction | PASS |
| `BREVO_SENDER_EMAIL` must be present | C14.2B.2: enforced before transport construction | PASS |
| All 4 gates tested in unit suite | C14.2B.2: 15 tests, 0.012s, all OK | PASS |

### 1.2 Recipient Guard at Provider Boundary

| Check | Evidence | Verdict |
|---|---|---|
| Acceptance mode rewrites recipient to test mailbox | C14.2A.2: mock-tested; HTTP call suppressed when test recipient absent | PASS |
| Missing test recipient returns `PERMANENT_FAILURE` before HTTP | C14.2A.2: `ACCEPTANCE_RECIPIENT_NOT_CONFIGURED` without reaching `post_json()` | PASS |
| Production mode preserves original recipient | C14.2A.2: existing behavior unchanged | PASS |
| Adapter regression suite | C14.2A.2: 23/23 PASS across C12.1, C12.2, C12.3 | PASS |

### 1.3 Live Execution Path Reached the Network Boundary

| Check | Evidence | Verdict |
|---|---|---|
| Adapter called `_send_once()` | C14.2B.4: `BREVO_NETWORK_ERROR` requires the transport-error path inside `_send_once()` | PASS |
| `urlopen()` began an outbound attempt | C14.2B.4: the real `UrllibBrevoHttpClient` produces `BREVO_NETWORK_ERROR` only from its `urlopen()` try block | PASS |
| Endpoint is correct | C14.2B.4: `https://api.brevo.com/v3/smtp/email`, assembled from fixed base + path | PASS |
| Error classification is correct | C14.2B.4: `RETRYABLE_FAILURE / NETWORK_ERROR / BREVO_NETWORK_ERROR` is the correct boundary mapping for transport failure | PASS |

### 1.4 Worker Termination Behavior

| Check | Evidence | Verdict |
|---|---|---|
| C13 Worker maps `NETWORK_ERROR` to terminal `FAILED` | C14.2B.4: no retry scheduled or executed | PASS |
| No automatic retry loop exists | C14.2B.4: C13 has no automatic retry implementation | PASS |
| Terminal `FAILED` is correct for ambiguous delivery | C14.2B.4: a timeout cannot prove Brevo did not receive the request; retry would be unsafe | PASS |

### 1.5 Send Path Isolation

| Check | Evidence | Verdict |
|---|---|---|
| No CRM Lead creation/update in path | C14.2B.0: static inspection confirms path excludes CRM writes | PASS |
| No EmailEvent lifecycle change | C14.2B.0: confirmed absent | PASS |
| No batch, scheduler, daemon, or campaign | C14.2B.0: confirmed absent | PASS |
| Queue is in-memory only | C14.2B.2: no durable persistence, no distributed idempotency | ACCEPTED |
| Worker is explicit single-item | C14.2B.2: `SendExecutionWorker.process(one QueueItem)` | PASS |

### 1.6 Code Artifacts Under Test

| Artifact | Tests | Status |
|---|---|---|
| `BrevoProviderAdapter` (recipient guard, error mapping) | C12.1, C12.2, C12.3 suites: 23/23 | PASS |
| `UrllibBrevoHttpClient` (HTTP transport) | C12.2 mock-HTTP suite | PASS |
| `phase3c14_2b_live_runner.py` (safety gates) | 15 tests, 0.012s | PASS |
| `SendExecutionWorker` (single-item dispatch) | Exercised through runner integration | PASS |

---

## 2. Should C14.2B Be Retried, Frozen, or Modified?

### Option A: Retry in a Different Network Environment

**REJECTED for now.** Rationale:

- The prior `BREVO_NETWORK_ERROR` occurred after `urlopen()` began — delivery state is ambiguous. A timeout or TLS EOF cannot prove Brevo did not receive any portion of the request.
- C14.2B.5 established that the current environment is `NETWORK_BLOCKED`: DNS and TCP/443 work, but Brevo TLS produces `SSLEOFError` on both proxy and no-proxy paths.
- Environment remediation is an operator/network concern, not a code concern. Retrying from the same environment without remediation would produce the same result.
- Retrying from a different environment is a valid future action, but it is not a code-phase decision.

### Option B: Mark Blocked by Environment and Proceed to C14.3

**SELECTED.** Rationale:

- C14.2B's code path is fully validated to the network boundary. The failure is external.
- C14.3 (CRM lifecycle acceptance) does not depend on a successful Brevo send. It validates CRM-side state transitions, hooks, and entity behavior — all of which are independent of the outbound email transport.
- Freezing C14.2B with a clear re-entry condition preserves the evidence and allows parallel or sequential progress.
- No code change is needed to proceed.

### Option C: Modify Code or Network Handling

**REJECTED.** Rationale:

- The adapter error classification (`BREVO_NETWORK_ERROR` → `RETRYABLE_FAILURE` → `NETWORK` → terminal `FAILED`) is correct. It distinguishes transport failure from auth, validation, rate-limit, and provider HTTP failures.
- The C13 Worker's no-retry behavior is correct for ambiguous delivery.
- The runner's safety gates (acceptance mode, test recipient, dry-run default) are correct and independently tested.
- The endpoint is correct (`https://api.brevo.com/v3/smtp/email`).
- Adding retry logic, proxy configuration, or TLS workarounds would complicate the adapter without addressing the root cause (an environmental network restriction).
- The `SSLEOFError` observed in C14.2B.5 is produced by Python's `ssl` module at the TLS record layer — it is not a code-configuration defect.

---

## 3. Confirmation: No Code Changes Required

### 3.1 Brevo Adapter (`brevo_provider.py`)

**No change needed.**

- `BrevoProviderAdapter._send_once()` correctly maps `BrevoTransportError` and `TimeoutError` to `RETRYABLE_FAILURE / NETWORK_ERROR / BREVO_NETWORK_ERROR`.
- The recipient guard at `BrevoProviderAdapter.send()` correctly intercepts before `_send_once()`.
- `BrevoConfiguration` correctly reads `BREVO_ACCEPTANCE_MODE` and `BREVO_TEST_RECIPIENT`.
- The fixed endpoint `https://api.brevo.com/v3/smtp/email` is correct.

### 3.2 C13 Worker (`worker_execution.py`)

**No change needed.**

- `SendExecutionWorker.process()` correctly dispatches a single `QueueItem` through the provider adapter.
- It correctly maps `NETWORK_ERROR` to terminal `FAILED` without retry.
- No automatic retry, batch, or scheduling logic exists to modify.

### 3.3 CRM Lifecycle

**No change needed.**

- The C14.2B runner uses a synthetic in-memory `SendExecution` ID. It does not touch CRM Leads, EmailEvents, DraftApprovals, ReplyEvents, or SendExecutions.
- The C14.2B.0 static inspection confirmed no CRM side effects in the send path.

### 3.4 HTTP Client (`brevo_http.py`)

**No change needed.**

- `UrllibBrevoHttpClient.post_json()` correctly constructs the POST request with `api-key` header and JSON body.
- It correctly wraps `URLError` as `BrevoTransportError` and `HTTPError` as `BrevoHttpResponse`.
- The 10-second timeout is appropriate for a one-shot acceptance request.
- The `SSLEOFError` observed in C14.2B.5 occurs inside Python's `ssl` module during the TLS handshake — it is not a client-code defect.

---

## 4. Remaining Acceptance Requirement Before Final C14.2B PASS

C14.2B can be closed as PASS only when **all** of the following are true:

### 4.1 Environment Remediation (Operator Action)

- [ ] A stable TLS path from the host to `api.brevo.com:443` is confirmed.
- [ ] At least two consecutive credential-free HTTPS root probes (`https://api.brevo.com/`) return consistent results (HTTP 404 or 200, not `SSLEOFError` or `URLError`).
- [ ] The remediation is documented with the specific change made (network, proxy, firewall, or VPN).

### 4.2 Runtime Preflight (Repeat C14.2B.0)

- [ ] All four environment variables are present in the runner's process:
  - `BREVO_API_KEY`
  - `BREVO_SENDER_EMAIL`
  - `BREVO_TEST_RECIPIENT`
  - `BREVO_ACCEPTANCE_MODE=true`
- [ ] Preflight verdict is `READY_FOR_C14_2B`.

### 4.3 Dry-Run Validation (Repeat C14.2B.2 dry-run)

- [ ] `--dry-run` exits with `C14_2B_RUNNER=READY` (not `BREVO_ACCEPTANCE_MODE_NOT_TRUE`).
- [ ] `LIVE_SEND=NOT_INVOKED` is printed.
- [ ] Recipient-before-guard and recipient-after-guard are printed and the after-guard value matches `BREVO_TEST_RECIPIENT`.

### 4.4 Controlled Live Execution

- [ ] `--execute-live` is invoked exactly once.
- [ ] The runner prints `MODE=EXECUTE_LIVE`.
- [ ] The runner prints `PROVIDER_RESULT: success=TRUE`.
- [ ] The runner prints a non-empty `EXTERNAL_MESSAGE_ID`.
- [ ] No CRM side effects, batch sends, or retries occur.
- [ ] The full execution is documented in a `PHASE3C14_2B_7_LIVE_ACCEPTANCE_CLOSURE.md` report.

### 4.5 Closure Documentation

- [ ] The closure report confirms all four sub-conditions above.
- [ ] The final verdict is `C14_2B=PASS`.
- [ ] The external message ID is recorded (no other payload or credential data).

---

## 5. Decision Summary

| Question | Answer |
|---|---|
| Is the code path validated? | Yes — all safety gates, guard logic, error classification, and worker termination are confirmed by test and by the single live attempt reaching `urlopen()`. |
| Is the failure in the code? | No — the failure is an environmental TLS restriction (`SSLEOFError`) on the Brevo path, confirmed by C14.2B.5. |
| Should we retry now? | No — environment is blocked; retry would be unsafe (ambiguous delivery) and futile (same TLS failure). |
| Should we modify code? | No — adapter, worker, HTTP client, and CRM lifecycle are all correct. |
| Should C14.3 proceed? | Yes — C14.3 (CRM lifecycle acceptance) is independent of outbound email transport. |
| What unblocks C14.2B? | Environment-level TLS/egress remediation by the operator, followed by a fresh preflight → dry-run → single `--execute-live`. |

---

## 6. C14.3 Handoff

C14.3 scope (CRM lifecycle acceptance) includes:

- DraftApproval entity, hook, and layout validation
- ReplyEvent entity, hook, and layout validation
- SendExecution entity, hook, and layout validation
- CRM-side state transitions independent of outbound transport

None of these depend on a successful Brevo API call. C14.3 can begin immediately.

The C14.2B re-entry point is documented in Section 4 above. When the environment is remediated, return to C14.2B.0 and follow the sequence through C14.2B.7 closure.

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-14 | Initial decision: FREEZE_C14_2B_AND_PROCEED |
