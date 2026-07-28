# Phase3C20 WP1.0 — AI Platform Skeleton Charter

## 1. Status

**Status:** Draft — Pending Human Owner Approval
**Phase:** Phase3C20 WP1.0
**Type:** Governance boundary only

This charter authorizes no implementation by itself. Human Owner approval is
required before WP1 implementation begins.

## 2. Baseline

- **Branch:** `master`
- **Baseline commit:** `61725d7` — *phase3c20: reconcile WP0 exit documentation after release repair*
- **WP0 exit tags:** `v1.9.13-alpha` and `phase3c20-wp0-exit`
- **Governing decision record:** ADR-C20 remains authoritative; this charter does
  not amend it.

## 3. Purpose

Define the bounded governance contract for an AIPlatform skeleton. WP1 is a
custody-and-boundary phase, not a provider-execution phase. Its sole product
surface is an administration location for externally held credential references.

## 4. WP1 Scope

Subject to human approval, WP1 may create only:

- `Modules/AIPlatform` skeleton structure;
- a reference-only `ProviderCredential` custody surface; and
- **Administration → AI Platform → Credentials**.

The skeleton may carry boundary metadata that identifies AIPlatform as an
isolated module boundary. That metadata is declarative only: it is not a
runtime marker service, hook implementation, transition owner, or provider
integration.

## 5. Non-goals

WP1 creates none of the following:

- provider execution or runtime AI execution;
- provider adapters, capability ports, or HTTP transport;
- `SearchProvider`, `EnrichmentProvider`, or `CompletionProvider`;
- `AIJob`, `AIRequestLog`, `PromptTemplate`, or `AIScore`;
- email workflow, Prospecting changes, queue changes, or lifecycle changes;
- provider models, routes, health routing, usage logging, or a health dashboard;
- a credential `status` enum, activate/deactivate lifecycle, credential
  transition service, or audit-hook implementation.

## 6. Architecture Boundary

AIPlatform remains isolated from Prospecting. WP1 does not read, write, route,
score, qualify, transition, or queue Prospecting records.

Any WP1 isolation marker is boundary metadata only. It documents module
ownership and supports later invariant verification; it does not authorize a
provider call, secret lookup, background job, scheduler, transition, or hook.

## 7. ProviderCredential Custody Model

`ProviderCredential` is a reference-only administrative custody surface. It may
hold only the following fields:

- `providerKey`
- `credentialReference`
- `displayName`
- `fingerprint`
- `lastFour` — externally supplied only
- `environment`
- `ownerUser`
- `rotationDueAt`
- `lastRotatedAt`
- `description`

It must never define or persist:

- `apiKey`
- `apiSecret`
- `token`
- `password`
- `plaintextCredential`
- `encryptedSecret`
- `decryptedValue`

`credentialReference` is an external-custody pointer only. It is write-only in
EspoCRM and must not be returned by record reads, list responses, API payloads,
exports, logs, exceptions, reports, or dashboards. WP1 does not dereference,
decrypt, validate, rotate, or execute against that reference.

Reference custody is intentionally retained: administrators can record which
external credential is governed without moving any provider secret into
EspoCRM.

## 8. Administration Surface

The entire WP1 administration surface is:

```text
Administration
└── AI Platform
    └── Credentials
```

WP1 creates no Administration entries for Providers, Models, Routes, Prompt
Templates, Usage Logs, or Health Dashboard.

## 9. Security Requirements

- EspoCRM never stores, decrypts, exposes, logs, exports, or returns provider
  secrets.
- `credentialReference` remains an external reference and is not readable after
  submission.
- `lastFour` is accepted only when externally supplied; WP1 must not derive it
  from a secret.
- No provider HTTP transport, SDK invocation, secret-manager lookup, or secret
  validation is permitted.
- No audit hook is implemented in WP1. Audit policy and any future audit
  mechanism require separately approved scope.

## 10. Invariant Ownership

WP1 activates, after approval and implementation:

- **C20-INV-01** — AIPlatform isolation marker.
- **C20-INV-04** — no plaintext credential exposure.

WP1 preserves without modification:

- **C20-INV-02**
- **C20-INV-03**
- **C20-INV-14**
- **C20-INV-15**
- **C20-INV-18**
- **C20-INV-19**
- **C20-INV-21**
- **C20-INV-22**

This charter does not modify the ADR or Invariant Registry; it assigns the
intended WP1 responsibility boundary only.

## 11. Testing Requirements

No tests are created by this governance document. Before any WP1 implementation
can exit, approved tests must demonstrate that:

- AIPlatform remains isolated from Prospecting;
- only the allowed custody fields exist;
- forbidden secret fields do not exist;
- `credentialReference` is absent from all readable, list, API, export, log,
  exception, report, and dashboard surfaces;
- no provider execution, transport, adapter, job, queue, lifecycle, or audit
  hook has been introduced.

## 12. Exit Criteria

WP1 may be considered complete only when all of the following are true:

1. Human Owner approval is recorded below.
2. The implemented scope is limited to the approved skeleton, custody surface,
   and administration path.
3. C20-INV-01 and C20-INV-04 have approved, passing enforcement evidence.
4. No forbidden secret storage or readable credential reference exists.
5. No non-goal in this charter has been introduced.
6. Required release and freeze review has been completed under separately
   approved release governance.

## 13. Release Governance

This document creates no release artifact, manifest change, version bump, tag,
or commit authorization. Any WP1 implementation and release must be reviewed
as a separate change after Human Owner approval.

## 14. WP2 Blocking Statement

ADR-C20 §11.1 remains unresolved. WP2 is fully blocked.

This charter does not authorize provider ports, provider adapters,
`CompletionProvider`, `EnrichmentProvider`, or runtime AI execution. It also
does not authorize HTTP transport, provider credential resolution, or any other
provider integration.

## Human Owner Approval Record

**Approved by:** Charles

**Date:** 2026-07-28

**Decision:**

I approve the Phase3C20 WP1 AIPlatform Skeleton Charter.

This approval authorizes WP1 only.

It does not accept ADR-C20.
It does not resolve ADR-C20 §11.1.
It does not authorize WP2 implementation.

WP2 remains blocked until separate human ratification.
