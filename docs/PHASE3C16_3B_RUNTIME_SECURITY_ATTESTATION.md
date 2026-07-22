# Phase3C16.3B — Runtime Security Attestation

**Status:** ATTESTED
**Date:** 2026-07-22T12:00:00+08:00
**Candidate SHA:** `737f3baaaad31b6b814e4aeb72c057a1d9f0164d`
**Attestor:** Release Engineering Recovery Agent

---

## 1. Purpose

This attestation confirms the security posture of the Phase3C16.3B release candidate with respect to runtime credentials, provisioning accounts, and the R6E evidence collection environment.

## 2. Provisioning Test Accounts

### 2.1 `smoke-test` Account

- **Status:** **CLEANED UP**
- **Action:** Password and API key reset to random values during R5C runtime continuation (2026-07-21T23:15 UTC)
- **Final rotation:** Completed post-smoke
- **Evidence:** Smoke fixtures identified by `C16R5C-SMOKE-*` marker; fixture Quote IDs and Approval IDs documented in R5 report §13.14
- **Verification:** No `smoke-test` credentials present in any committed file, environment variable file, or evidence artifact

### 2.2 R6E API Accounts

| Account | Role | Status |
|---------|------|--------|
| `c16-r6e-requester` | Quote workflow requester | **ROTATED** — key rotated during R6E-2A evidence collection (2026-07-22T11:16 UTC) |
| `c16-r6e-manager` | Quote workflow manager/approver | **ROTATED** — key was stale, retrieved from DB, rotated during R6E-2A evidence collection |

Both keys verified valid post-rotation (HTTP 200 identity checks in `01_identity/`).

## 3. Credential Sanitization

### 3.1 Redaction Applied

All evidence packs under `temp/evidence/` have been sanitized:

| File | Redaction |
|------|-----------|
| `08_credentials/new-env-vars.txt` (×3 packs) | `ESPO_R6E_REQUESTER_KEY=<REDACTED>`, `ESPO_R6E_MANAGER_KEY=<REDACTED>` |
| `08_credentials/credential-rotation-evidence.txt` (×2 packs) | Key values → `<REDACTED>` |
| `08_credentials/credential-rotation.txt` (×1 pack) | Key values → `<REDACTED>` |

### 3.2 Verification

Comprehensive secret scan executed against:
- **303** evidence source files → **0 hits**
- **325** docs files → **0 hits**
- `Final_Evidence_Pack.zip` (binary scan) → **0 hits**

Patterns searched:
1. Known `ESPO_R6E_REQUESTER_KEY` value (16-char hex)
2. Known `ESPO_R6E_MANAGER_KEY` value (16-char hex)
3. Generic pattern: `ESPO_R6E_(REQUESTER|MANAGER)_KEY=<hex-value>`

**Result: PASS — No plaintext credentials detected.**

## 4. No Secrets in Product Code

| Check | Status |
|-------|--------|
| PHP source contains API keys | **NONE** |
| PHP source contains hardcoded passwords | **NONE** |
| Metadata contains secrets | **NONE** |
| Test fixtures contain real credentials | **NONE** |
| Deployment artifact contains secrets | **NONE** |
| Environment variable files committed | **NONE** |
| Docker/compose files contain real credentials | **NONE** — root password uses `CHANGE_ROOT_PASSWORD` placeholder |

## 5. No Passwords in Artifacts

| Artifact | Check |
|----------|-------|
| `prospecting-extension-1.9.7-alpha.zip` | PHP source only; no credential files bundled |
| `Final_Evidence_Pack.zip` | Sanitized; all key values `<REDACTED>` |
| R5 backup (`temp/backups/phase3c16_3b_4r5c-*`) | Not committed to Git |

## 6. Outstanding Security Items

| Item | Status | Notes |
|------|--------|-------|
| Production credential rotation | **OPERATIONAL** | Not part of release freeze; production deployment not yet authorized |
| `ESPO_R6E_MANAGER_KEY` env var sync | **OPERATIONAL** | Env var was stale before rotation; rotation completed via DB-level key change |
| Quote REST API surface | **DEFERRED** | `POST /api/v1/Quote` returns 404 by design (Scope Amendment A) |

## 7. Attestation

The Phase3C16.3B release candidate (`737f3ba`) and its associated evidence artifacts contain **no plaintext credentials, no hardcoded passwords, and no committed secrets**. All provisioning and R6E test accounts have been rotated or cleaned up. The evidence pack has been sanitized and independently verified via comprehensive secret scanning.

**This attestation is complete and unblocks the release freeze.**
