# Railway DP-WP1 Deterministic Extension Installation Charter

| Field | Value |
| --- | --- |
| Status | CHARTER COMPLETE — IMPLEMENTATION NOT AUTHORIZED |
| Work package | DP-WP1 — Deterministic Extension Installation |
| Repository baseline reviewed | `8ede18ebd26984b516eefac4f6c8facb32068f01` |
| Governing deployment model | Model B — deterministic repository overlay |
| Prerequisite | DP-WP0 ratified and committed |

## 1. Purpose

The Railway base image can start EspoCRM, connect to MySQL, and serve a login page. That proves infrastructure bootstrap only; it does not prove that the Chitu C16–C25 extension is registered, installed, migrationally current, or restart-safe. DP-WP1 defines the controlled installation process that will turn a verified EspoCRM base runtime and verified DP-WP0 artifacts into a verifiably installed extension state.

This is a charter and implementation plan. It does not authorize implementing or running an installer, executing `AfterInstall.php`, mutating a database, deploying to Railway, or changing runtime configuration.

## 2. Governance Basis and Non-Redefinition Rule

DP-WP1 is governed by the ratified full deployment plan, its ratification record, the DP-WP0 Deployment Contract, and the DP-WP0 ratification record. DP-WP0 is **RATIFIED AND COMMITTED**; DP-WP1 is **ELIGIBLE — NOT AUTHORIZED**.

DP-WP1 consumes but must not redefine the following DP-WP0 decisions:

- canonical backend and frontend roots;
- the artifact manifest, its hashes, and its check procedure;
- extension name and version derived from `crm-extension/manifest.json`;
- the immutable release identity and its authorized source baseline;
- source-of-truth exclusions, including local Docker code volumes and local/Railway databases.

In particular, no installation workflow may copy a stale local code volume over repository artifacts, import a local database as a deployment image, or treat mutable runtime state as release source.

## 3. Installation Model and Boundaries

The intended model is:

```text
EspoCRM 10.0.1 base runtime
  + DP-WP0-verified repository overlay and manifest
  + explicit, locked, ledgered installation runner
  = registered, validated extension installation state
```

The runner must accept only a successful manifest verification, a matching extension identity, and an explicitly selected release identity. It must be an explicit administrative deployment action, never an implicit Apache/container-start action.

The following are prohibited as installation inputs or primary installation mechanisms:

- persistent runtime volumes, local code volumes, local database dumps, uploads, preferences, caches, logs, or sessions;
- manual browser setup as the primary path or evidence of completion;
- undocumented environment/configuration edits;
- business data, provider credentials, email delivery, external API calls, autonomous workflows, or background lifecycle activation.

## 4. Controlled Installation Lifecycle

Each lifecycle phase must record its result in the installation ledger and fail closed. A later phase must not begin after a failed or unresolved earlier phase.

### A. Preflight

Before any mutation, the runner must:

1. run the DP-WP0 manifest check and validate the exact manifest bytes;
2. read extension name and version from `crm-extension/manifest.json` and compare them with the manifest release identity;
3. verify the selected Git release identity and reject an unrecognized or mismatched input set;
4. verify required writable directories and minimum file permissions without broadening access; and
5. acquire the installation lock and inspect prior ledger state.

Any preflight failure must create or update a failed attempt record without executing registration, migrations, metadata rebuild, or provisioning.

### B. Extension Registration and State Discovery

The runner must discover the existing EspoCRM module/extension registration and installed-version state before changing it. It must distinguish absent, matching-complete, matching-incomplete, failed, and version-mismatched states.

Registration must bind the extension name, extension version, artifact-manifest hash, and source Git commit as one release identity. A complete matching installation is a no-op after validation; it must not duplicate registration or repeat completed steps. A different version or identity is a blocking condition until an explicitly authorized upgrade/rollback design exists.

### C. Reviewed `AfterInstall.php` Classification

The current `crm-extension/scripts/AfterInstall.php` contains two observable actions: extension-owned `numbering_sequence` table initialization and EspoCRM metadata rebuild.

| Hook action | DP-WP1 classification | Required future control |
| --- | --- | --- |
| `CREATE TABLE IF NOT EXISTS numbering_sequence` | Conditionally allowed deterministic extension-owned schema preparation | Execute only as a named, versioned, locked, ledgered migration/installation step after preflight; do not invoke it as opaque startup code. |
| `DataManager::rebuild()` | Conditionally allowed deterministic metadata refresh | Execute only after verified artifacts and successful required database steps; record result and validate postconditions. |

No external API, provider credential, email, business-data, autonomous lifecycle, or irreversible uncontrolled operation is presently represented in that hook. Such actions are forbidden in DP-WP1. The future implementation must either expose the two permitted operations as explicit runner steps or prove that an adapter invokes the hook only under the same lock, identity checks, ledger, and failure handling. This charter authorizes neither approach yet.

### D. Migration Runner Contract

DP-WP1 defines the installation/migration-runner contract, not the full C16–C25 schema migration set. Full reviewed C16–C25 schema implementation remains DP-WP4-owned.

For every executable DP-WP1 step, the future runner must require:

- a stable step identifier and declared ordering;
- one installation lock covering state discovery through completion or failure recording;
- a content checksum for the step definition;
- a durable per-step ledger result; and
- an explicit expected postcondition.

The runner must reject checksum changes, out-of-order execution, duplicate execution, unknown prior steps, and identity changes for an in-progress release. It must not silently infer success from the presence of a table or cache artifact.

### E. Cache and Metadata Refresh Validation

After all permitted required steps complete, the runner may rebuild EspoCRM metadata and clear/refresh only the application cache necessary for that rebuild. It must then validate that the matching extension is registered, the ledger is complete, and metadata can load without installation errors. Cache refresh must not activate provider integrations, generate business records, send email, or serve as a substitute for later browser validation.

## 5. Durable Installation Ledger

DP-WP1 implementation must introduce an extension-owned durable installation ledger. Its canonical attempt record must contain at least:

| Field | Requirement |
| --- | --- |
| `installationId` | Unique immutable attempt identifier. |
| `extensionName` | Value derived from the verified manifest. |
| `extensionVersion` | Value derived from the verified manifest. |
| `artifactManifestHash` | SHA-256 identity of the verified DP-WP0 manifest. |
| `sourceGitCommit` | Verified release Git commit from the manifest. |
| `installedAt` | Controlled completion timestamp; unset until completion. |
| `status` | At minimum: `planned`, `running`, `completed`, `failed`, or `blocked`. |
| `executedSteps` | Ordered named step identifiers with checksum, start/end state, and outcome. |
| `failureReason` | Redacted diagnostic code and concise cause; never a credential or business payload. |

The ledger must be transactionally or otherwise durably updated before and after each mutation. It must preserve prior attempts for auditability, use a release-identity uniqueness rule to prevent multiple completed records for the same identity, and retain an explicit incomplete/failed state rather than overwriting it. The lock owner and step execution model must make concurrent starts fail or wait safely; they must never create duplicate installation work.

## 6. Failure Recovery and Rollback Boundary

An interrupted attempt must be detected from its durable `running` or incomplete step state. Resume is allowed only through the controlled runner, under the same verified release identity and lock, beginning at a step whose recorded postcondition has been revalidated. The runner must not re-run a completed step merely because the process restarted.

| Condition | Required result |
| --- | --- |
| Manifest, version, or source-commit mismatch | Block before mutation and record the reason. |
| Partial migration/installation step failure | Record failed state and step diagnostic; stop with no silent continuation. |
| Interrupted process | Preserve incomplete state; allow controlled identity-matching resume only. |
| Concurrent execution | Refuse or serialize via lock; no duplicate work. |
| Installation rollback | Limited to installation registration/state and reviewed non-destructive compensations. No database restore, production rollback, full deployment rollback, or data import is in DP-WP1 scope. |

If recovery cannot prove the prior state and postcondition safely, it must block for operator review rather than guess.

## 7. Security and Data Boundary

DP-WP1 must be self-contained and offline with respect to business systems. It may not read, write, expose, or log provider credentials, customer/business data, uploads, user preferences, sessions, or secret-bearing configuration. It may not call external services, send email, enable outreach, execute providers, or activate autonomous runtime behavior.

Only least-privilege database and filesystem access needed for the reviewed installation steps may be used. Failure records and test fixtures must use synthetic/non-secret information. Any required secret or environment change is outside this charter and needs separate authorization and ownership.

## 8. Work-Package Ownership

| Work package | Ownership boundary |
| --- | --- |
| DP-WP0 | Canonical artifact manifest, release identity, and verification boundary. |
| DP-WP1 | Deterministic extension registration, controlled installation runner, ledger, lock, hook classification, and failure/restart safety. |
| DP-WP2 | Roles, teams, ACL assignments, navigation, dashboards, and reviewed provisioning. |
| DP-WP3 | Safe branding recovery, allowlisting, and branding delivery. |
| DP-WP4 | Fresh database bootstrap, C16–C25 schema/migrations, and synthetic-data policy. |
| DP-WP5 | Railway integration, release command, persistent-volume behavior, health, and backups. |
| DP-WP6 | Automated, container/database, and browser validation. |
| DP-WP7 | Deployment evidence, independent closure review, and final closure. |

DP-WP1 must not absorb downstream work by adding roles, ACLs, navigation, dashboards, branding, broad database rebuilds, Railway changes, browser validation, or deployment closure.

## 9. Implementation Exit Criteria

Separate DP-WP1 implementation authorization may be considered complete only when all of the following are evidenced:

- a reviewed runner validates the DP-WP0 manifest before mutation;
- verified extension identity is registered and recorded in the durable ledger;
- lock, checksum, ordering, idempotence, mismatch, interruption, and partial-failure behavior are automated-tested;
- reviewed `AfterInstall.php` actions are constrained to named ledgered steps or an equivalent controlled adapter;
- cache/metadata refresh has explicit validation and cannot re-trigger completed installation work;
- no provider credential, business data, email, external call, or autonomous lifecycle behavior exists in the installation path;
- the implementation remains inside the ownership boundary; and
- independent review passes.

## 10. Authorization Boundary

This document does not authorize implementation. DP-WP1 remains **ELIGIBLE — NOT AUTHORIZED** until a separate implementation authorization is issued. DP-WP2 through DP-WP7 remain **NOT AUTHORIZED**. No user-facing/browser claim may be used as evidence that this charter's installation model has been implemented.
