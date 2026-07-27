# Architecture Decision Records (ADR)

**Status:** Index and template only — no historical ADRs retroactively marked as Accepted

## Purpose

ADRs capture **durable architectural decisions** with context, options, and consequences. They complement phase reports:

| Artifact | Focus |
|----------|-------|
| **Phase report** | What was done, verification, file list, verdict |
| **ADR** | Why a boundary or design choice persists across phases |

## When to Write an ADR

- Cross-cutting boundary changes (extension vs connector vs engine)
- Contract version bumps
- Security or ACL model changes
- Persistence semantics (e.g. GET-then-PUT claim vs atomic API)

## Naming

```text
docs/adr/NNNN-short-title.md
```

Example: `docs/adr/0001-no-automatic-opportunity.md`

Use four-digit zero-padded sequence.

## Status Values

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion; not yet implemented |
| **Accepted** | Decision active in codebase |
| **Superseded** | Replaced by newer ADR (link both ways) |
| **Deprecated** | No longer recommended |

Do not mark **Accepted** without code or manifest evidence.

## Template

```markdown
# ADR NNNN: Title

**Status:** Proposed | Accepted | Superseded | Deprecated  
**Date:** YYYY-MM-DD  
**Supersedes:** (optional ADR link)  
**Superseded by:** (optional ADR link)

## Context

What problem or constraint forces a decision?

## Decision

What we chose.

## Consequences

Positive, negative, and follow-up work.

## Evidence

- Source files
- Tests
- Phase report links
```

## Phase-scoped ADRs (actual practice)

Phase ADRs use `ADR-C{N}_…` / `ADR-C{N}-A{M}_…` filenames for consistency with
accepted siblings. The numeric `NNNN-short-title.md` convention above remains the
README template; reconciling the two is a docs-only C20 WP0 item.

| ADR | Status | Path |
| --- | --- | --- |
| ADR-C18-A6 | Accepted | [ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md](ADR-C18-A6_SEND_RECOVERY_ACTION_BOUNDARY.md) |
| ADR-C19 | Accepted (Amended) | [ADR-C19_REPLY_EVENT_LIFECYCLE.md](ADR-C19_REPLY_EVENT_LIFECYCLE.md) |
| ADR-C20 | Proposed | [ADR-C20_AI_PLATFORM_ARCHITECTURE.md](ADR-C20_AI_PLATFORM_ARCHITECTURE.md) |

### ADR-C20 (Proposed)

- **Marker:** `adr-c20-aiplatform-v1`
- **Baseline:** `phase3c19-freeze` @ `4a7a111` (`1.9.12-alpha`)
- **Scope:** AI Platform module, provider abstraction, `AIJob` lifecycle, advisory
  `AIQualificationInsight` architecture (§6.4 — non-authoritative dynamic qualification
  layer with required provenance; no `AIScore`; Chitu owns canonical scoring)
- **Constraint:** WP0 documentation only — no runtime/code/artifact authorization;
  §11.1 human ratification required before WP2
- **Header style:** Status / Date / Phase / Decision Owners / Related / Acceptance
  record aligned with ADR-C18-A6 and ADR-C19

## Suggested ADR Topics (Not Yet Written)

These are **candidates only** — not accepted decisions in this index:

1. `NO_AUTOMATIC_OPPORTUNITY` on proposal sync
2. Vendored contract import boundary (no Chitu app runtime)
3. GET-then-PUT SearchJob claim for single-runner MVP
4. Email body exclusion from CRM storage
5. SearchStrategy fingerprint deduplication vs global job uniqueness
6. Separate acquisition pipeline from ChituSyncService

## Related Documents

- [../reports/README.md](../reports/README.md)
- [../architecture/BOUNDARIES.md](../architecture/BOUNDARIES.md)
- [ADR-C20_AI_PLATFORM_ARCHITECTURE.md](ADR-C20_AI_PLATFORM_ARCHITECTURE.md)
