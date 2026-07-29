# Phase3C20 Open-Source Reference Decisions

## Status

**Status:** Frozen decisions for controlled C20 extension work
**Date:** 2026-07-29
**Scope:** Design and governance reference only; this document imports no external code

## Work-Package Designation

The C20 charter defines one active **WP2 — Capability Ports** work package. Its
recorded sub-deliveries are WP2.1 (protocol foundation) and WP2.2 (adapter
implementation). WP2.1 and WP2.2 are complete at the audit baseline.

The repository does not define a formal `WP2.3` label. The reviewed C20 audit
material identifies the next additive work as **`WP-C20-AUDIT-01` — Capability
Registry Resolution**, explicitly as a **C20 WP2 extension**. This document
uses that recorded designation rather than inventing a new numbered WP.

The extension remains bound by the active WP2 charter: connector-side only; no
PHP, JavaScript, metadata, CRM-side orchestration, provider-route UI, health
checks, autonomous dispatch, scoring, lifecycle authority, or email delivery.

## Decision Principles

1. EspoCRM remains the business, policy, ACL, approval, and record authority.
2. The connector is the sole provider-I/O boundary, but is not a configuration
   authority and must not select providers outside CRM-authorized bindings.
3. Chitu retains scoring, ICP, qualification, and research authority.
4. A reference pattern is not authorization to copy its implementation,
   licensing model, persistence model, or runtime architecture.
5. The current extension is a deterministic in-memory resolution contract; it
   does not make a provider call, add a transport, or persist runtime state.

## ADOPT

| Reference | Decision | C20 interpretation and boundary |
|---|---|---|
| YALC | Capability Registry Resolution | Adopt a deterministic capability-and-purpose resolver, but restrict its candidates to CRM-authorized provider bindings. The registry cannot discover, persist, or authorize providers. |
| DeskcommCRM | Append-only execution audit | Adopt as a future WP3/C22 governance principle for execution logs. This extension creates no ledger or database enforcement. |
| DeskcommCRM | Rules born paused | Adopt as a future C22 automation rule: newly created rules require explicit review before activation. No automation rule is created here. |
| DeskcommCRM | Action-level ledger | Adopt as a future C22 execution-governance direction. Reuse existing ACL, workflow authorization, transition-service, and mutation-guard authority rather than creating a parallel authorization system. |
| DeskcommCRM | Human handoff | Adopt as a future C22 governance pattern: handoff is explicit, attributable, and audit-visible. |
| OpenOutreach | Enrichment cost gate | Adopt as a future policy principle: enrichment spend must be subject to governance and approval before irreversible outreach work. No cost gate or limiter is implemented here. |
| OpenOutreach | ProspectCandidate / formal Lead separation | Adopt as a future C21 modeling principle while preserving the existing `ProspectPool` and `Lead` authority. No candidate entity is created here. |
| B2B SDR Agent Template | HEARTBEAT to read-only Pipeline Inspector | Adopt only as a future read-only inspection/dashlet concept. It does not authorize an agent, queue, scheduler, or pipeline mutation. |

## ADAPT

### Provider rate limit

- EspoCRM owns policy and governance configuration.
- The connector may own future real-time counts, windows, tokens, and
  concurrency state.
- This extension permits only contract-level availability and `retry_after`
  inputs. It creates no limiter, counter, cache, Redis dependency, or CRM
  `ProviderRateLimit` entity.

### Append-only enforcement

- First-stage enforcement belongs in service, API, ACL, guard, and test
  boundaries.
- Database privileges or triggers are a later deployment-hardening decision.
- This work must not execute a database `REVOKE` or make schema-level changes.

### Intelligence lifecycle

- Confidence and validation state remain separate concepts.
- `hypothesis`, `validated`, and `proven` must not be stored in a confidence
  field.
- A universal `PROVEN` value is not authorized as an AI research conclusion.

### Action permission

- Extend existing ACL, `WorkflowAuthorizationService`, transition-service, and
  mutation-guard authority when a later WP requires it.
- Do not create a parallel permission or agent-authorization system.

### Outbound validator

- Future policy outcomes are `ADVISORY`, `REQUIRES_APPROVAL`, and `HARD_BLOCK`.
- A normal operator may not override `HARD_BLOCK`.
- No outbound validator or send-path change is authorized in C20 WP2.

### Human handoff

- Future handoff uses explicit status fields and attributable state changes.
- Do not use an infinity timestamp as a handoff or suppression mechanism.

## DEFER

The following remain outside this C20 WP2 extension:

- GP active learning;
- an independent candidate-pool entity decision;
- `ChannelSession`;
- agent memory;
- WhatsApp provider work;
- Pipeline Inspector implementation;
- `AutomationRule`;
- `ActionLedger`;
- `CommunicationSuppression`.

## REJECT

The following are rejected for this repository and this extension:

- `CandidateScore` as CRM authority or a separate scoring entity;
- CLI, Markdown, or SQLite as business authority;
- direct MCP writes to CRM;
- connector selection of CRM-unauthorized providers;
- unreviewed YAML provider runtime configuration;
- copying OpenOutreach GPLv3 code into EspoCRM;
- WAHA in the core architecture;
- a self-chaining task queue replacing the existing queue architecture;
- autonomous agent lifecycle progression, quoting, or channel switching;
- external memory overriding EspoCRM facts.

## Capability Registry Resolution Boundary

The approved authority path is:

```text
EspoCRM ProviderBinding / request policy
        -> connector CapabilityRegistry
        -> only CRM-authorized provider candidates
        -> existing capability-port adapter
```

The registry is an in-memory selection and explanation component. It is not a
provider configuration store, credential resolver, health probe, rate limiter,
HTTP transport, scheduler, worker, or CRM write path.

Its contract must support capability, purpose, CRM-authorized bindings,
credential availability, health input, policy version, and request context. It
must return a deterministic, auditable selection or a normalized existing error
classification. Secret values are forbidden in both inputs and outputs.

## Licensing and Code-Borrowing Decision

### Reference posture

| Reference | License posture | Permitted use in this repository |
|---|---|---|
| YALC | Audit evidence identifies MIT at reviewed commit `ffc6e37` | Conceptual reference only for this extension; no source file is copied. A future code borrow requires re-verifying the specific source file and its effective MIT coverage at the pinned revision. |
| DeskcommCRM | Audit evidence identifies MIT at reviewed commit `4f83cdc3b202d161bfa59fd1ae44ddafeac72132` | Architectural reference only in this extension; no source file is copied. Any future code borrow requires file-specific MIT verification. |
| B2B SDR Agent Template | Audit evidence identifies MIT at reviewed commit `e71bfd4da4a56153ab5ef05a4bd684d370b8c90c` | Pattern reference only; no code is copied. Any future borrow requires file-specific MIT verification. |
| OpenOutreach | GPLv3 | Design reference or clean-room reimplementation only. No GPLv3 source code, derived source, or copied fragment may enter EspoCRM. |

### Mandatory conditions for any future MIT code reuse

1. Confirm the exact external file, revision, copyright notice, and effective
   MIT license coverage before copying or modifying it.
2. Preserve the required copyright and license notices in the derivative file
   or accompanying attribution material.
3. Record the source repository, revision, file path, copied range, adaptation
   scope, and retained attribution in the implementation report.
4. Adapt code to EspoCRM and connector boundaries; do not transplant a CLI,
   SQLite, YAML runtime, secret store, SDK, or HTTP transport wholesale.

### Current implementation disclosure

`WP-C20-AUDIT-01` will use an independent Python implementation. No external
source file, code fragment, or license notice is copied by this decision
document or by the accompanying registry implementation.

## Non-Authorization Record

This decision does not accept ADR-C20, activate WP3, or authorize new CRM
entities. In particular it does not authorize `AIJob`, `AIRequestLog`,
`ProviderRoute`, `ProviderHealth`, `Candidate`, `Lead`, C21/C22 entities,
Prospecting lifecycle changes, SendExecution authority changes, or real
provider egress.

## Decision Outcome

**APPROVED FOR CONTROLLED WP2 EXTENSION:** deterministic capability registry
resolution constrained to CRM-authorized provider bindings and existing WP2
capability ports.

All other reference patterns remain adopted only as future design direction,
adapted with the stated constraints, deferred, or rejected as recorded above.
