# C25 Railway Deployment Model

| Field | Value |
| --- | --- |
| Document Type | Operating-model record (documentation only) |
| Scope | Current Railway staging deployment operating model |
| Date | 2026-08-06 |
| Related baseline | `docs/audit/PHASE3C25_STAGING_BASELINE_ACCEPTANCE.md` |
| Status | **RECORDED — NO ACTION AUTHORIZED** |

```text
This document records the current Railway deployment operating model.

It does NOT authorize Railway configuration changes, source connection,
redeploy, production promotion, migration, or runtime mutation.
```

---

## 1. Objective

Document the current Railway deployment operating model for C25 staging so
operators and reviewers share one authoritative description of how code reaches
the staging service, what identity is currently running, and which governance
rules bound future deployment work.

---

## 2. Current Operating Model

Railway staging is an **execution environment** only. It builds and runs an
approved immutable image under explicit operator control. It has no GitHub
auto-deploy path and no authority to interpret git push as a deployment signal.

### 2.1 Source and trigger model

| Property | Current state |
| --- | --- |
| Railway `source.repo` | `null` |
| GitHub auto-deploy | Not configured / not used |
| Deployment trigger | Railway CLI (explicit operator invocation) |
| Git push → deploy | Does **not** occur |

Because `source.repo` is `null`, Railway is not connected to a GitHub
repository for continuous deployment. Pushing commits to GitHub does not
build, deploy, restart, or otherwise mutate the staging service.

### 2.2 Build model

| Property | Current state |
| --- | --- |
| Builder | `DOCKERFILE` |
| Dockerfile path | `deployment/railway/Dockerfile` |
| Build context | Repository root (as required by the Dockerfile) |

Declarative build hints in-repo (`deployment/railway/railway.toml`) match this
model: Dockerfile builder, Dockerfile path
`deployment/railway/Dockerfile`, healthcheck on `/`, and **no** start or
release command that would grant Railway lifecycle or migration authority.

### 2.3 Deployment path

1. Operator obtains explicit authorization for the intended deployment action.
2. Operator uses a frozen commit or tag as the deployment source.
3. Operator invokes Railway CLI to build from `deployment/railway/Dockerfile`
   and deploy the resulting image.
4. Runtime config changes (if any) are handled as a separate surface from code
   deployment and require their own authorization.

---

## 3. Current Staging Identity

Accepted C25 staging identity (read-only record; no redeploy implied):

| Field | Verified value |
| --- | --- |
| Project | `espocrm-c25` |
| Environment | `staging` |
| Service | `espocrm-c25-staging` |
| Deployment | `1dd8584c-f23a-45ba-89b6-51f2da95c2b1` |
| Image | `sha256:59d3c93b5eb67e5260b82664c0bfa460707d919da5b5119474826eed3559f819` |

This identity is the accepted staging baseline referenced by
`PHASE3C25_STAGING_BASELINE_ACCEPTANCE.md` and subsequent WP1 Railway sync
records. Recording it here does not change Railway state.

---

## 4. Governance Rules

The following rules define the C25 Railway deployment operating model:

### 4.1 Git push does not trigger deployment

A git push to any branch, including `main` or feature branches, does not
trigger a Railway build or deployment. Continuous deployment from GitHub is
out of model while `source.repo` remains `null`.

### 4.2 Deployment requires explicit authorization

No Railway build, deploy, restart, service create/update, or source-connection
action may proceed without a separate, written authorization for that action.
Presence of Dockerfile assets, `railway.toml`, or this operating-model document
is not deployment authorization.

### 4.3 Frozen commits / tags are deployment sources

Authorized deployments consume frozen commits or tags as the deployment source.
Mutable working-tree state, uncommitted changes, and ad-hoc branch tips are not
deployment sources. Image identity is bound to immutable digests; mutable tags
alone are insufficient.

### 4.4 Runtime config is separated from code deployment

Runtime configuration changes (for example EspoCRM UI Tab List /
`config.tabList`, environment variables, or volume-backed config) are a
distinct change surface from code image deployment. They:

- require their own authorization;
- must not be smuggled into a code redeploy without that authorization; and
- must not be treated as evidence that a new image was deployed (or vice versa).

---

## 5. Boundary and Restrictions

This documentation task and this record honor:

| Restriction | Status |
| --- | --- |
| No Railway configuration changes | Honored |
| No source connection (`source.repo` remains disconnected) | Honored |
| No redeploy | Honored |

Out of scope for this document:

- connecting a GitHub repository to Railway;
- enabling auto-deploy or watch paths;
- changing builder, Dockerfile path, start/release commands, or healthcheck;
- building or deploying a new image;
- restarting the staging service;
- production promotion;
- migration, registration, provisioning, or `AfterInstall` execution.

---

## 6. Related Records

| Record | Role |
| --- | --- |
| `docs/audit/PHASE3C25_STAGING_BASELINE_ACCEPTANCE.md` | Accepted staging identity and runtime baseline |
| `deployment/railway/README.md` | Execution-boundary description (deployment not authorized by that README) |
| `deployment/railway/railway.toml` | Declarative Dockerfile builder / healthcheck hints |
| `deployment/railway/Dockerfile` | Staging image build definition |
| `docs/audit/PHASE3C25_DP_WP5_RAILWAY_IMPLEMENTATION_FREEZE_CLOSURE.md` | DP-WP5 freeze / execution-boundary freeze |

---

## 7. Final Status

```text
C25 Railway Deployment Model: RECORDED

source.repo = null
GitHub auto-deploy = not used
Deploy path = Railway CLI + explicit authorization
Builder = DOCKERFILE
Dockerfile = deployment/railway/Dockerfile

Staging deployment = 1dd8584c-f23a-45ba-89b6-51f2da95c2b1
Staging image     = sha256:59d3c93b5eb67e5260b82664c0bfa460707d919da5b5119474826eed3559f819

Railway configuration: unchanged
Source connection: unchanged
Redeploy: not performed
```
