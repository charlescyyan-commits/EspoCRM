# Phase 3A-2.2-B Runtime Verify Report

**Date:** 2026-07-11  
**Scope:** Prove auth chain only — Chitu Intelligence → EspoCRM API User → `X-Api-Key` → `GET /api/v1/App/user`  
**Business code modified:** NO  
**CRM writes:** NONE (no Lead / ResearchEvidence create or delete)

---

## 1. Discovery Result

### `integration/espocrm_sync/`

| File | Role |
|---|---|
| `real_client.py` | Library: `LocalEspoCRMClient` — localhost-only REST client |
| `real_sync.py` | `run_local_synthetic_sync()` — live workflow that **writes** synthetic Lead/Evidence |
| `client.py` | Offline mock EspoCRM client |
| `mapper.py`, `gate.py`, `contract.py`, `idempotency.py`, `audit.py`, `models.py` | Sync adapter internals |
| `__init__.py` | Exports `LocalEspoCRMClient` |

### Callers of `LocalEspoCRMClient`

| Path | Live EspoCRM? | Writes? |
|---|---|---|
| `tests/test_espocrm_real_client.py` | NO (stubbed `_request`) | NO |
| `integration/espocrm_sync/real_sync.py` | YES | YES — forbidden for this verify |
| `real_client.py` CLI / `__main__` | **Does not exist** | — |

### Design of `real_client.py`

- Not a CLI. No `if __name__ == "__main__"`.
- Intended as an importable client for env-gated local test sync.
- Auth: `ESPOCRM_TEST_API_KEY` → header `X-Api-Key` → `GET App/user`.
- Also supports Basic/`Espo-Authorization` when username/password env vars are set.
- `preflight()` reads Metadata only (no writes) but requires Prospecting extension schema.

### Why user commands behaved as observed

| Command | Result | Cause |
|---|---|---|
| `python integration/espocrm_sync/real_client.py` | `ModuleNotFoundError: No module named 'integration'` | **A** — package import path; must run from repo root as a package |
| `python -m integration.espocrm_sync.real_client` | Loads, **no output** | **B** — library module with no `__main__` / no prints |

### Correct execution entry (auth-only)

There is **no** existing live auth-only CLI. Correct usage is import + call:

```python
from integration.espocrm_sync.real_client import LocalEspoCRMClient
client = LocalEspoCRMClient.from_environment()
client.authenticate()  # GET /api/v1/App/user
client.preflight()     # GET Metadata (read-only; needs extension)
```

Do **not** use `run_local_synthetic_sync()` for auth-only checks.

---

## 2. 执行命令

### Offline existing tests (mocked)

```powershell
cd D:\Chitu-intelligence
python -m unittest tests.test_espocrm_real_client -v
```

### Live auth chain (read-only; no product file changes)

```powershell
cd D:\Chitu-intelligence
# If Cursor/terminal was started before User env vars were set, reload them or restart shell.
python -c "from integration.espocrm_sync.real_client import LocalEspoCRMClient; c=LocalEspoCRMClient.from_environment(); c.authenticate(); print('AUTH_OK'); u=c._request('GET','App/user'); print(u.get('user',{}).get('userName')); c.preflight()"
```

---

## 3. Runtime Result

| Item | Value |
|---|---|
| Python interpreter | `C:\Users\98624\AppData\Local\Programs\Python\Python312\python.exe` |
| Python version | 3.12.10 |
| Working directory | `D:\Chitu-intelligence` |
| `ESPOCRM_TEST_ENV` | present = YES, value = `true` |
| `ESPOCRM_TEST_API_KEY` | present = YES, length = 32 (**key not printed**) |
| `ESPOCRM_TEST_URL` | present = NO → client default `http://localhost:8080` |
| Env note | User-scope Windows vars exist; this Cursor process needed User-registry reload because it was started before the vars were set |

### Existing unittest

```text
Ran 9 tests in 0.153s
OK
```

These tests prove safety/env parsing with stubs. They do **not** hit live EspoCRM.

### Live client construction

| Step | Result |
|---|---|
| `LocalEspoCRMClient.from_environment()` | PASS |
| `base_url` | `http://localhost:8080` |
| auth mode | `api_key` |

---

## 4. API 认证结果

| Step | Result |
|---|---|
| `authenticate()` | **PASS** |
| Endpoint | `GET http://localhost:8080/api/v1/App/user` |
| Header | `X-Api-Key` (from `ESPOCRM_TEST_API_KEY`) |
| HTTP status | **200** (implied by successful JSON response; no `LocalEspoCRMError`) |
| Response keys | `acl`, `appParams`, `language`, `preferences`, `settings`, `token`, `user` |
| `user.userName` | `chitu_ai_connector` |
| `user.type` | `api` |
| `token` present | NO (normal for API-key auth) |
| `acl` present | YES |

**Auth chain verdict:** PASS

`Chitu Intelligence → EspoCRM API User → X-Api-Key → /api/v1/App/user` is working.

### `preflight()` (read-only metadata)

| Step | Result |
|---|---|
| `preflight()` | **FAIL** |
| Error | `EnvironmentSafetyError: local EspoCRM extension schema does not match the approved skeleton` |

This is **not** an API Key failure. Auth already succeeded. The live CRM lacks Prospecting extension Lead `pe*` fields / `ResearchEvidence` / `researchEvidences` link.

---

## 5. Failure 分类

| Code | Category | Applies? |
|---|---|---|
| A | Python package/import问题 | YES for `python …/real_client.py`; NO for `-m` / repo-root import |
| B | 测试入口缺失 | YES — no live auth-only CLI/`__main__`; unittest is mocked only |
| C | API Key认证失败 | **NO** — `authenticate()` PASS, API user returned |
| D | EspoCRM权限失败 | NO evidence of 403 on `App/user` |
| E | Schema/metadata不匹配 | **YES** — `preflight()` FAIL |

Primary goal (auth chain): **PASS**  
Secondary gate (`preflight`): **FAIL → E**

---

## 6. 下一步建议

1. Restart Cursor/terminal so `ESPOCRM_TEST_ENV` / `ESPOCRM_TEST_API_KEY` are inherited without registry reload.
2. Treat auth as restored: API User `chitu_ai_connector` + `X-Api-Key` works.
3. Install Phase 3A-2.1 `espocrm_extension` into the local EspoCRM test instance and rebuild metadata/cache.
4. Re-run read-only `preflight()` until schema matches.
5. Only after preflight PASS, authorize synthetic sync (`run_local_synthetic_sync`) under existing safety rules.

Do not add `main()` to `real_client.py` in this phase unless explicitly authorized as a separate task.
