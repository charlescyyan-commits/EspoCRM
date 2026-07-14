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
