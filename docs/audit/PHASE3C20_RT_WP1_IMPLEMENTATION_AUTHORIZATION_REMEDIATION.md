# Phase3C20 RT-WP1 Implementation Authorization Remediation

| Field | Value |
| --- | --- |
| Review mode | Independent governance remediation |
| Date | 2026-08-02 |
| Decision | OPTION C — COMMERCIAL_BRIEF IS PURPOSE, NOT CAPABILITY |
| Runtime implementation performed | None |
| Authorization change | None |

## 1. Executive Decision

```text
OPTION C — COMMERCIAL_BRIEF IS PURPOSE, NOT CAPABILITY
```

`CommercialBrief` is a C25 business artifact and governed workflow output. A
request to generate it is a business use case and execution intent. Neither
fact alone establishes a distinct, reusable provider capability.

This decision does not map Commercial Brief to `DRAFT_ASSISTANCE`, does not
register `commercial_brief_generation`, and does not authorize a fifth enum
value. The present C20 record does not define `DRAFT_ASSISTANCE` broadly enough
to absorb the structured Commercial Brief output without an unapproved semantic
expansion. Any later choice of the existing technical capability, or a
demonstrated need for a new one, remains a separate C20 decision.

## 2. Repository Verification

| Check | Result |
| --- | --- |
| Branch | `master` |
| Local HEAD | `f0f49ab043d5fcaf555dbcd767817b1f873f3071` |
| `origin/master` | `f0f49ab043d5fcaf555dbcd767817b1f873f3071` |
| Remote `master` | `f0f49ab043d5fcaf555dbcd767817b1f873f3071` |
| RT-WP1 ratification tag target, local | `f0f49ab043d5fcaf555dbcd767817b1f873f3071` |
| RT-WP1 ratification tag target, remote | `f0f49ab043d5fcaf555dbcd767817b1f873f3071` |
| Staged-file count before remediation | 0 |
| Existing dirty worktree | Unrelated modified and untracked content preserved without change |

## 3. Formal Definition of CompletionCapability

### Authority source

`docs/adr/ADR-C20-005_COMPLETION_CAPABILITY_PORTFOLIO.md` and
`chitu-connector/chitu_connector/acquisition/providers/completion/base.py`
are authoritative for the current portfolio.

### Exact definition

`CompletionCapability` is the exhaustive, ratified `CompletionProvider`
portfolio. It is the type carried by `CompletionRequest` and
`CompletionResult`, and it selects one of the adapter's declared provider
function contracts. It is separate from the generic registry family
`Capability.COMPLETION` and separate from a string `purpose` evaluated by
`CapabilityRegistry` against binding policy.

### Current values

```text
RESEARCH_EVIDENCE
QUALIFICATION_INSIGHT
DRAFT_ASSISTANCE
REPLY_ASSISTANCE
```

### What capability is not

It is not a C25 business entity, caller motive, ProviderBinding purpose,
provider-selection key, CRM lifecycle stage, scoring/ranking value, or output
schema. A capability declaration does not grant routing, dispatch, credential
access, or provider invocation.

## 4. Formal Meaning of DRAFT_ASSISTANCE

The Completion Provider scope defines `DRAFT_ASSISTANCE` as AI-assisted draft
generation for operator review: proposed email content, talking points, and
follow-up suggestions. Its stated output is editable draft text presented to an
operator, within the existing DraftApproval boundary. It does not modify the
Chitu email-generation engine and does not send email.

The current enum, adapter `_SYSTEM_PROMPTS`, and fixture tests implement that
same bounded meaning. No reviewed authority source states that it covers an
immutable, evidence-anchored CommercialBrief, its C25 review/disposition model,
its provenance contract, or its append-only audit requirements.

Commercial Brief therefore does not fit `DRAFT_ASSISTANCE` without a semantic
expansion. This remediation does not make that expansion.

## 5. Commercial Brief Classification

| Dimension | Classification | Evidence |
| --- | --- | --- |
| Business entity | Yes | C25 WP2 Charter and ADR-C25-007 define `CommercialBrief` and its C25 audit relationship. |
| Workflow output | Yes | C25 WP2.2 describes generation and validation of a governed brief. |
| Provider capability | No current determination | C20 has not ratified an independent capability, and C25 cannot decide C20 portfolio placement. |
| Purpose / execution intent | Yes | A request to generate a commercial brief is a business use within a future C20 binding-policy path. |
| Output schema | Yes, C25-owned | C25 defines structured content, provenance, review, and audit constraints; these do not define a provider capability. |
| Lifecycle object | Yes, C25-owned | Review/disposition and audit lifecycle belong to C25, not CompletionProvider. |

The proposed identifier `commercial_brief_generation` remains only a proposed
binding purpose. It is distinct from `CommercialBrief`, from any C20 capability
name, and from a provider model or adapter name.

## 6. Option Analysis

### Option A — No New Capability

**Supporting evidence:** the existing four-value portfolio is authoritative,
and a purpose is independently evaluated by `CapabilityRegistry`.

**Contradiction:** the formal `DRAFT_ASSISTANCE` contract is limited to draft
text and operator review in the DraftApproval boundary. It does not establish
that C25's structured CommercialBrief may be represented by that value.

**Architecture and compatibility impact:** reusing `DRAFT_ASSISTANCE` now
would silently widen the enum's documented semantics and adapter prompt
contract. It would provide neither a valid ProviderBinding nor C25 generation
authority.

**C25 impact:** C25 WP2.2 remains NO GO. Option A cannot unlock it.

**Result:** not selected.

### Option B — New CompletionCapability

**Supporting evidence:** C25 records `COMMERCIAL_BRIEF` as a proposed C20
portfolio candidate, and a new enum value would preserve a distinct adapter
prompt and serialized contract if C20 later establishes an independent,
reusable technical capability.

**Contradiction:** repository and governance evidence do not show a
cross-module provider capability distinct from C25's business use case. The
current name is C25-specific, while ADR-C20-005 says it is proposed only and
requires independent C20 approval.

**Architecture and compatibility impact:** a fifth value would affect the enum,
request/result contract, adapter prompt mapping, fixture coverage, unknown-value
handling, external connector compatibility, and rolling deployment behavior.
It must remain non-routable without an authorized binding and later dispatch.

**C25 impact:** C25 WP2.2 remains NO GO even if a portfolio amendment later
passes, because ProviderBinding delivery and invariant activation remain
separate C20 dependencies.

**Result:** not selected. A later evidence-backed case may be considered only
through `Phase3C20 CompletionCapability Portfolio Amendment`.

### Option C — Purpose, Not Capability

**Supporting evidence:** `CapabilityRegistry` separates the enum family from a
string `purpose`; it evaluates `allowed_purposes` and rejects disallowed use
with `PURPOSE_NOT_ALLOWED`. C25 identifies CommercialBrief as its own business
artifact, lifecycle object, and output contract. C25 expressly owns no provider,
routing, dispatch, credential, or capability-portfolio authority.

**Contradiction:** the existing sources do not identify which of the current
four technical capability contracts would execute a future commercial-brief
request. This is a deliberately retained C20 decision, not a basis for inferred
`DRAFT_ASSISTANCE` support.

**Architecture and compatibility impact:** no enum, adapter, registry, or
serialization change follows from classifying CommercialBrief as a purpose and
C25 output. Provider selection remains binding-policy work under RT-WP2; actual
execution remains later dispatch work.

**C25 impact:** C25 WP2.2 remains NO GO until the capability mapping is
separately decided, ProviderBinding and purpose delivery exist, and the
required C20 invariant activation and verification gates pass.

**Result:** selected.

## 7. Selected Option

Option C best fits the current governance boundary. It resolves the prior
implementation-authorization error: the ratified RT-WP1 Charter's conditional
reference to a possible `COMMERCIAL_BRIEF` enum extension is not a requirement
to add one. The condition remains unfulfilled and does not create code scope.

This classification does not decide the future technical capability mapping.
If C20 later establishes that the Commercial Brief output requires a distinct,
reusable provider function, Option B must be evaluated through the separate
portfolio-amendment process. Until then, no fifth capability is implied.

## 8. RT-WP1 Charter Impact

| Question | Result |
| --- | --- |
| Charter validity | Remains valid. It preserves the four values and makes an enum addition conditional on separate authorization. |
| Charter amendment | Not required for the present classification. No text claims the fifth value is mandatory or already ratified. |
| Charter ratification | Remains valid. |
| Implementation scope | No code-bearing RT-WP1 scope remains under the current four-value contract. |
| RT-WP1 status | Implementation remains NOT AUTHORIZED. |

RT-WP1 requires a no-code scope reconciliation before any exit or status claim.
That task must confirm the conditional enum candidate is not an authorized
deliverable and must not recast this remediation as runtime implementation.

## 9. RT-WP1 Authorization Impact

```text
RT-WP1 Implementation: NOT AUTHORIZED
```

The original blocker is resolved as an interpretation issue, not by granting
an enum extension. No runtime implementation authorization follows because the
selected Option C leaves no approved code unit.

The prerequisite to close the RT-WP1 scope is:

```text
Phase3C20 RT-WP1 No-Code Scope Reconciliation
```

Any future request for a distinct provider capability requires independent C20
portfolio evidence and a separate amendment process.

## 10. C25 WP2.2 Impact

```text
C25 WP2.2: NO GO
```

Selection of Option C does not release C25. C25 generation remains blocked
until all independently governed conditions are satisfied:

1. C20 records the technical capability mapping or, if necessary, separately
   ratifies a portfolio amendment.
2. RT-WP2 delivers the authorized ProviderBinding and allowed-binding surface.
3. The matching purpose is registered through the approved binding contract.
4. C20 resolves the INV-06 and INV-10 runtime gaps.
5. C20-INV-05 through C20-INV-11 are activated and independently verified.
6. C25 records the completed dependency closure before separately considering
   WP2.2 authorization.

## 11. Findings

| Severity | Finding |
| --- | --- |
| BLOCKER | NONE for this classification decision. |
| HIGH | NONE. |
| MEDIUM | The C25 dependency package retains `COMMERCIAL_BRIEF` as a proposed C20 candidate. It is non-authoritative for C20 portfolio placement and must remain conditional during the RT-WP1 no-code scope reconciliation. |
| LOW | NONE. |
| INFORMATIONAL | The worktree carries unrelated modified and untracked material; it was preserved. |
| INFORMATIONAL | C25 generation remains blocked by ProviderBinding delivery and deferred C20 invariant gates independently of this classification. |

## 12. Repository Change Verification

| Check | Result |
| --- | --- |
| File created | `docs/audit/PHASE3C20_RT_WP1_IMPLEMENTATION_AUTHORIZATION_REMEDIATION.md` only |
| Existing files modified by this task | None |
| Code, metadata, tests, or plans | None |
| Stage / commit / push / tag | None |
| `git diff --check` | PASS |
| Marker scan | PASS; no prohibited unresolved markers |
| Staged-file count | 0 |

## 13. Exact Next Task

```text
Phase3C20 RT-WP1 No-Code Scope Reconciliation
```
