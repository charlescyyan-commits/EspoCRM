# Getting Started

**Status:** Static Verified

## Repository Purpose

`EspoCRM-Production` packages:

1. **CRM Extension** — EspoCRM module for prospecting, sync APIs, acquisition workspace.
2. **Chitu Connector** — Python client for sync and acquisition job execution.
3. **Deployment assets** — ZIP artifacts and provisioning scripts.

## Quick Orientation

| If you need to… | Start here |
|-----------------|------------|
| Understand system layout | [../architecture/SYSTEM_OVERVIEW.md](../architecture/SYSTEM_OVERVIEW.md) |
| Find API routes | [../api/REST_ENDPOINTS.md](../api/REST_ENDPOINTS.md) |
| Build extension ZIP | [../deployment/PACKAGE.md](../deployment/PACKAGE.md) |
| Run offline tests | [TESTING.md](TESTING.md) |
| Read phase history | [../reports/README.md](../reports/README.md) |

## Pre-Work Checklist

1. Confirm branch and working tree: `git status --short`
2. Read `AGENTS.md` / `CLAUDE.md` workspace boundaries
3. Do not modify Chitu scoring, AI research, or email-generation engines
4. Keep connector independent — import only `chitu_connector` and vendored interfaces

## Allowed vs Forbidden

**Allowed:** Extension development, connector integration, deployment docs, tests, provisioning documentation.

**Forbidden:** Unrelated Chitu app changes, real customer data import, production outreach without approval, modifying EspoCRM core in this repo.

## Current Phase Snapshot

| Area | State |
|------|-------|
| CRM sync (Lead/Evidence/Feedback/Brevo) | **Implemented** |
| Acquisition metadata (SearchStrategy/Job/Pool) | **Implemented** |
| Job runner (fake provider + Espo REST) | **Implemented** (offline tests) |
| Live search providers (Google/Apify) | **Not Implemented** |
| ProspectPool → Lead bridge | **Not Implemented** |

## Related Documents

- [LOCAL_SETUP.md](LOCAL_SETUP.md)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
