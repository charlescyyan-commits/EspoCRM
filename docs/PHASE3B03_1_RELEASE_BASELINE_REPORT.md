# Phase3B03.1 — Release Package Finalization & Git Baseline Report

**Date:** 2026-07-12  
**Workspace:** `D:\EspoCRM-Production`  
**Scope:** Release ZIP + manifest/SHA verification + Production Git baseline  
**Constraints observed:** No Phase3B04; no business-logic / contract / Chitu / entity / workflow / sync behavior changes.

---

## 1. ZIP Release Status

| Field | Value |
|---|---|
| Status | **PASS** — release artifact created |
| Filename | `prospecting-extension-1.3.1-alpha.zip` |
| Path | `D:\EspoCRM-Production\deployment\prospecting-extension-1.3.1-alpha.zip` |
| Size | 20262 bytes |
| Created | 2026-07-12 21:09:17 (+0800) |
| Build script | `crm-extension/scripts/build_release_package.ps1` |
| Entries | 33 (manifest + `files/` only) |
| Forbidden content in ZIP | None (no tests/debug/temp/secrets/cache) |

Included categories: manifest, entityDefs, layouts, metadata, API routes, connector sync integration (`ChituSyncService` + PostSync*), workflow hook (`LeadWorkflowHook`).

Detail record: `docs/PHASE3B03_RELEASE_ARTIFACT.md`

---

## 2. Manifest Check

| Location | Version | Result |
|---|---|---|
| `crm-extension/manifest.json` | `1.3.1-alpha` | PASS |
| ZIP root `manifest.json` | `1.3.1-alpha` | PASS |
| Consistency | Identical | **PASS** |

---

## 3. SHA256

| Field | Value |
|---|---|
| Filename | `prospecting-extension-1.3.1-alpha.zip` |
| Size | 20262 bytes |
| Created time | 2026-07-12 21:09:17 |
| SHA256 | `BD6D4CDB3F36DC3E77108C52F48795E8DD5E0E31B3F5619FDB570FF1B4845354` |

---

## 4. Git Initialization Result

| Step | Result |
|---|---|
| Prior `.git` | Empty placeholder (not a valid repo) |
| Action | Removed placeholder; ran `git init` |
| `.gitignore` | Created (logs, cache, `__pycache__`, `.env`/secrets, `node_modules`, vendor temps, DB dumps, `temp/`, local tooling dirs) |
| Branch | `master` |

Committed paths (baseline): `.gitignore`, root docs (`AGENTS.md`, `CLAUDE.md`, `README.md`), `crm-extension/`, `chitu-connector/`, `chitu_connector/`, `deployment/` (including 1.3.1-alpha ZIP + older ZIPs + provisioning), `docs/`, `scripts/`.

Excluded by `.gitignore` (not committed): `__pycache__/`, `temp/`, `.agents/`, `.codex/`, secrets/env, DB dumps, etc.

---

## 5. Commit Hash

| Field | Value |
|---|---|
| Message | `Phase3B03 stable baseline` |
| Full hash | `b6f47b71b99fb64d78a59146874427481f910449` |
| Short hash | `b6f47b7` |
| Author | charlescyyan-commits \<charles.cyyan@gmail.com\> |
| Date | Sun Jul 12 21:09:47 2026 +0800 |
| Authority | If this file is amended into the same commit, prefer `git rev-parse HEAD` / `git log -1` as the live hash |

---

## 6. Working Tree Status

Verified after baseline commit:

```
On branch master
nothing to commit, working tree clean
```

`git log -1 --oneline` contains message:

```
Phase3B03 stable baseline
```

---

## Summary

| Item | Status |
|---|---|
| Release ZIP 1.3.1-alpha | PASS |
| Manifest source ↔ ZIP | PASS |
| SHA256 recorded | PASS |
| Git baseline initialized | PASS |
| Baseline commit | `b6f47b71b99fb64d78a59146874427481f910449` (`Phase3B03 stable baseline`) |
| Working tree clean (post-commit) | PASS |

**Phase3B03.1 complete. Stop. Do not enter Phase3B04.**
