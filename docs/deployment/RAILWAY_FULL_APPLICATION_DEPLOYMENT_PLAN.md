# Railway Full Application Deployment Plan

| Field | Value |
| --- | --- |
| Status | RATIFIED — IMPLEMENTATION REQUIRES SEPARATE DP-WP AUTHORIZATION |
| Ratification date | `2026-08-04` |
| Ratification verdict | PASS — COMPLETE DEPLOYMENT PLAN RATIFIED |
| Review verdict | PASS WITH INFORMATIONAL NOTES |
| Implementation state | NOT STARTED |
| First eligible work package | DP-WP0 — Deployment Contract and Artifact Manifest |
| DP-WP0 authorization state | NOT AUTHORIZED |
| Environment | Railway `espocrm staging` only |
| Web service | `espocrm-web` |
| Database service | `MySQL` |
| Public URL | `https://espocrm-web-production.up.railway.app` |
| Baseline | `11612feeffad170dd77c5f9f134457c268ce545e` |
| EspoCRM image | `espocrm/espocrm:10.0.1` |
| Extension version | `1.9.13-alpha` from `crm-extension/manifest.json` |

## 1. Purpose and non-goals

This plan defines a reproducible staging deployment of the repository's canonical C16–C25 EspoCRM application. It remedies the present code-only overlay deployment by introducing a versioned release identity, deterministic migrations, reviewed configuration provisioning, safe branding recovery, persistence checks, and rollback gates.

This document does not authorize implementation, Railway changes, database imports, branding extraction, provider configuration, email sending, data migration, production promotion, Git staging, commits, or pushes.

The local Docker code volumes are explicitly **not** a deployment source. They are stale and partial compared with the repository and must never be copied over repository code.

## 2. Target staging architecture

```text
Project: espocrm staging
Environment: staging
├── espocrm-web
│   ├── image built from the authorized Git commit
│   ├── Apache/PHP EspoCRM 10.0.1
│   └── persistent volume: /var/www/html/data
└── MySQL
    └── dedicated staging database
```

Required Railway settings:

| Concern | Required target |
| --- | --- |
| Build source | Authorized Git commit on `master` |
| Dockerfile | `deployment/railway/Dockerfile` with repository-root build context |
| Healthcheck | HTTP `/` plus application check during release validation |
| Storage | Only `/var/www/html/data` persisted; never mount all of `/var/www/html` |
| Database binding | Dedicated staging MySQL through Railway secret references |
| Public URL | The stated Railway URL, classified as staging |
| Restart behavior | Web startup is lightweight; migrations/provisioning are ledger-gated and not rerun blindly |
| Backup boundary | MySQL snapshot, data-volume snapshot, configuration/navigation snapshot before mutation |

If Railway labels the environment as production, rename it to staging before final validation. This is an administrative prerequisite, not an application change.

Production promotion is out of scope. It requires a separate approved security, data, provider, and operational readiness process.

## 3. Source-of-truth policy

| Category | Authoritative source | Rule |
| --- | --- | --- |
| Backend code | `crm-extension/files/custom` | Repository wins over local Docker volumes |
| Frontend code | `crm-extension/files/client/custom` | Repository wins over local Docker volumes |
| Extension version | `crm-extension/manifest.json` | Must match release artifact and migration ledger |
| C25 schema | Repository entity metadata and reviewed migrations | Do not derive from the incomplete local database |
| Numbering sequence | Reviewed equivalent of `crm-extension/scripts/AfterInstall.php` | Must be explicit and ledgered |
| Roles and ACL defaults | Reviewed version-controlled provisioning | Do not clone local user assignments |
| Teams | Reviewed staging provisioning | Create only required staging teams |
| Navigation | Version-controlled navigation definition | Do not rely on browser edits |
| Dashboards | Version-controlled safe defaults | Do not migrate personal dashboards by default |
| Branding assets | Selectively recovered and approved data-volume assets | No full config/data export |
| Application name/theme | Explicit non-secret staging settings | Separate from credentials |
| Business data | Synthetic staging data only | No wholesale local DB import |
| Provider credentials | Excluded | Remain unset |
| User preferences | Not migrated by default | Seed only approved role-neutral defaults |
| Local MySQL | Reference only | Use for schema/config design, not as a deployment image |

## 4. Canonical release model

### Selected model: deterministic overlay plus explicit migration runner

**Model B** is selected. The image continues to contain the canonical repository overlay, while a separate, versioned migration runner installs schema and safe configuration exactly once per migration. This model is preferred because it cleanly separates the Apache lifecycle from migration/provisioning and does not depend on undocumented UI uploads or manual copies.

Model A (installing an EspoCRM ZIP extension during bootstrap) remains a valid fallback only if it can be made fully deterministic in a non-interactive environment. It would require the package to include `manifest.json`, the complete `files/` tree, and the install hook; it must not use the currently stale release ZIP without regeneration and verification.

Release contract:

1. Canonical files are the 612 tracked files under `crm-extension/files` at the authorized commit.
2. Build a release manifest containing relative path, SHA-256, bytes, commit, extension version, and build timestamp.
3. Regenerate the installable ZIP from the same commit when ZIP distribution is retained; reject any ZIP whose manifest differs from the canonical file manifest.
4. Record the Git commit and extension version in the image labels and the migration ledger.
5. The Docker image copies only canonical overlay files; it must not consume host-mounted or local Docker-volume code.

Required future implementation artifacts:

| Artifact | Purpose | Classification |
| --- | --- | --- |
| Release manifest | Detect missing/stale code | Source-controlled/generated release evidence |
| Migration runner | Execute ledgered schema/config migrations | Source-controlled code |
| Migration ledger table | Record execution state | Staging database state |
| Safe config definition | Application name/theme/defaults | Internal configuration |
| Branding manifest | Allowlisted files, hashes, source provenance | Internal configuration |

## 5. Bootstrap phases and execution boundaries

| Phase | Activities | Execution point | Repeat policy |
| --- | --- | --- | --- |
| 1. Filesystem preparation | Verify overlay, normalize permissions, create needed data directories, redact logs | Image build and normal entrypoint | Safe verification every start; no destructive sync |
| 2. Installation-state detection | Inspect DB connectivity, EspoCRM installation markers, ledger state, incomplete migration lock | Explicit release/migration command | Every migration invocation |
| 3. Schema and metadata | Apply reviewed migrations, create numbering sequence, rebuild metadata, clear generated cache | One-shot migration runner | Ledger-gated only |
| 4. Safe configuration | Roles, teams, ACL defaults, navigation, dashboards, staging labels/theme | One-shot migration runner | Version-gated/idempotent only |
| 5. Validation | Schema/module/ACL/navigation/branding/health checks | CI plus explicit release validation | Every deployment validation |

### Phase 1 — filesystem preparation

- Verify expected backend and frontend overlay manifests before Apache starts.
- Keep `/var/www/html/custom` and `/var/www/html/client/custom` image-owned, not volume-backed.
- Persist only `/var/www/html/data`.
- Ensure web-user ownership only for runtime-writable data paths.
- Normalize shell scripts to LF during image build.
- Never log secret values, full configuration files, cookies, request headers, or database DSNs.

### Phase 2 — deterministic state detection

Detection must combine all of the following; a single file is insufficient:

- MySQL connectivity and target database existence;
- EspoCRM installation state in the data volume;
- presence and status of the migration ledger;
- installed extension/version state, when available;
- expected base tables and current schema version;
- an incomplete migration lock or failed ledger row;
- manifest checksum compatibility with the running image.

Classify the result as fresh install, initialized/compatible, upgrade required, or partially failed. A partially failed state must fail closed and require an explicit recovery path; it must not continue into Apache startup as if successful.

### Phase 3 — schema and metadata order

1. Acquire a database advisory lock scoped to the staging application.
2. Verify release manifest and ledger compatibility.
3. Ensure the EspoCRM base installation has completed.
4. Apply reviewed extension-owned migrations, including the `numbering_sequence` equivalent.
5. Run EspoCRM rebuild to materialize entity metadata and tables.
6. Clear only generated cache/compiled metadata after the rebuild.
7. Validate required C16–C25 tables and metadata before configuration provisioning.
8. Mark the ledger row successful only after validation passes.
9. Release the advisory lock.

### Phase 4 — safe configuration provisioning

Only reviewed, versioned, idempotent defaults may run here:

- essential staging teams and roles;
- approved ACL mappings;
- canonical navigation;
- role-neutral dashboard defaults;
- explicit non-secret staging application name/theme;
- approved branding manifest and assets.

Synthetic users, synthetic records, cleanup scripts, credential changes, provider activation, email/outreach activation, mass reassignment, and business-data operations are excluded.

### Phase 5 — validation

Validation must prove module presence, routes, schema, ACL, navigation, branding, health, restart persistence, and staging isolation before browser validation begins.

## 6. Migration ledger and idempotency

Use both an extension-owned database table and EspoCRM extension state where available. The table is the deterministic execution authority; EspoCRM extension state is cross-check evidence.

Suggested ledger fields:

| Field | Purpose |
| --- | --- |
| `migration_id` | Immutable ordered identifier, e.g. `dp-001-schema-core` |
| `extension_version` | Manifest version |
| `git_commit` | Full authorized source commit |
| `artifact_sha256` | Canonical release manifest hash |
| `started_at`, `finished_at` | Audit timing |
| `status` | `started`, `succeeded`, `failed`, `rolled_back` |
| `error_class` | Redacted failure category only |
| `executor` | Release runner identity, not a secret |

Migration classifications:

| Class | Rule |
| --- | --- |
| Idempotent | Safe to rerun; checks desired end state |
| Insert-if-missing | Creates named, non-personal staging defaults only |
| Update-if-version-older | Applies compatible definition revision with an explicit version guard |
| One-time | Cannot rerun after success; guarded by ledger and backup checkpoint |
| Destructive/prohibited | Never automatic; requires separate written authorization |
| Staging-only | May create marked synthetic fixtures; never part of core bootstrap |

Never run every provisioning script at every container start. The runner must use an advisory lock, one migration transaction where supported, bounded timeout, redacted logs, and an explicit failed-state recovery command.

## 7. Provisioning script review matrix

The 32 scripts under `deployment/provisioning/` must be reorganized into reviewed migration units before use. They are not automatically eligible merely because they exist.

| Script group | Purpose | Automatic bootstrap | Staging safe | Production safe | Notes |
| --- | --- | ---:|---:|---:| --- |
| `phase3a33_provision_roles.php` | Core role/team/test-user setup | No, extract role/team subset first | Conditional | No | Test users must be removed from core path |
| `phase3b01_*`, `phase3b02_*` provisioners | Entity-model/workflow roles | Conditional after review | Yes | No | Upsert patterns; dependencies must be explicit |
| `phase3b03_*` to `phase3b07_*` provisioners | Test users, feedback/email roles, workspace/default dashboards | No by default | Conditional | No | Several assume validation users or create synthetic state |
| `phase3c01_provision_acquisition_workspace.php` | Dashboard defaults | Conditional | Yes | No | Convert to role-neutral default migration |
| `phase3c02_1_provision_acquisition_acl.php` | Acquisition ACL defaults | Conditional | Yes | No | Review against C16–C25 governance |
| `phase3c11_2_provision_persistence_acl.php` | Persistence ACL defaults | Conditional | Yes | No | Version-gate after schema validation |
| `phase3c17_provision_operational_centers_navigation.php` | Canonical navigation | Yes, after conversion | Yes | No | Retain snapshot, dry-run, and restore behavior |
| `phase3c17_provision_sales_development_command_center.php` | Command Center dashboard | No until refactored | Conditional | No | Current local-test targeting is not a staging default |
| `phase3u04_provision_navbar_tab_order.php` | Deprecated navigation compatibility | No | No | No | Delegate only to the canonical C17 materializer |
| `phase_acl03_apply_sales_manager_field_visibility.php` | Sales-manager field visibility | Conditional | Yes | No | Requires role existence and scope review |
| `*_provision_synthetic_*`, `*_provision_*_test_user.php` | Synthetic validation fixtures | Never core bootstrap | Yes | No | Separate DP-WP4/DP-WP6 authorization |
| `*_cleanup_validation_records.php` | Remove synthetic records | Never automatic | Conditional | No | Destructive, marker-scoped, manual approval only |
| `phase3c10_6_check_research_evidence_duplicates.php` | Pre-rebuild check | Manual validation | Yes | No | Read-only gate, not a migration |

Core bootstrap may contain only reviewed roles, teams, ACL defaults, navigation, dashboards, and non-secret app defaults. Validation fixtures and cleanup remain separate staging-only work.

### Detailed script disposition

This table is the required disposition before any script is converted into a migration. `Core?` means eligible only after extraction into a reviewed, ledgered unit; it does not authorize execution of the current script unchanged.

| Script | Purpose/dependencies | Writes | Idempotency | Staging / production | Synthetic or destructive | Core? / manual authorization |
| --- | --- | --- | --- | --- | --- |
| `phase3a33_provision_roles.php` | Named roles, team, local test users | Roles, team, users, relations | Mostly upsert | Conditional / no | Test users | Extract role/team only; manual review |
| `phase3b01_cleanup_validation_records.php` | Remove B01 validation records | Records | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b01_provision_entity_model_roles.php` | Entity-model roles | Roles | Upsert | Yes / no | No | Core candidate after ACL review |
| `phase3b02_cleanup_validation_records.php` | Remove B02 fixtures | Leads/tasks/evidence/opportunities | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b02_provision_workflow_pipeline.php` | Workflow role setup; assumes test users | Roles/relations | Partial upsert | Conditional / no | Test-user dependency | Manual until refactored |
| `phase3b03_cleanup_validation_records.php` | Remove B03 fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b03_provision_connector_test_user.php` | Connector test identity | User/role relation | Insert/update | Yes / no | Test user | Staging validation only |
| `phase3b04_cleanup_validation_records.php` | Remove B04 fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b04_provision_feedback_test_user.php` | Feedback validation identity | User/role relation | Insert/update | Yes / no | Test user | Staging validation only |
| `phase3b05a_cleanup_validation_records.php` | Remove B05a fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b05a_provision_brevo_test_user.php` | Provider-era test identity | User/role relation | Insert/update | No by default / no | Provider-adjacent test | Never automatic; manual only |
| `phase3b05b_cleanup_validation_records.php` | Remove B05b fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b05b_provision_email_workflow_roles.php` | Email workflow role defaults | Roles | Upsert | Conditional / no | No | Manual ACL/governance review |
| `phase3b05c_cleanup_validation_records.php` | Remove B05c fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b05c_provision_email_feedback_roles.php` | Email feedback role defaults | Roles | Upsert | Conditional / no | No | Manual ACL/governance review |
| `phase3b06_1_cleanup_validation_records.php` | Remove B06.1 fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b06_1_provision_connector_test_user.php` | Connector test identity | User/role relation | Insert/update | Yes / no | Test user | Staging validation only |
| `phase3b06_cleanup_validation_records.php` | Remove B06 workspace fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b06_provision_synthetic_lead.php` | Controlled browser fixture | Lead/evidence/feedback | Insert-if-missing | Yes / no | Synthetic data | Staging validation only |
| `phase3b06_provision_workspace_roles.php` | Workspace roles/team/preferences | Roles, team, preferences | Upsert/merge | Conditional / no | May create users | Extract role/team/default subset |
| `phase3b07_cleanup_validation_records.php` | Remove B07 fixtures/users | Records/users | Destructive | Conditional / no | Cleanup | Never automatic; manual |
| `phase3b07_provision_operations_dashboards.php` | Dashboard preferences | Preferences | Merge/update | Conditional / no | User preference writes | Convert to safe role-neutral default |
| `phase3b07_provision_synthetic_records.php` | Operational fixture set | Synthetic business records | Insert-if-missing | Yes / no | Synthetic data | Staging validation only |
| `phase3b07_provision_validation_user.php` | Validation user | User/role relation | Insert/update | Yes / no | Test user | Staging validation only |
| `phase3c01_provision_acquisition_workspace.php` | Acquisition dashboard | Preferences | Merge/update | Conditional / no | User preference writes | Convert to safe default |
| `phase3c02_1_provision_acquisition_acl.php` | Search/acquisition ACL | Role data | Update existing roles | Yes / no | No | Core candidate after role matrix approval |
| `phase3c10_6_check_research_evidence_duplicates.php` | Pre-rebuild duplicate gate | None | Read-only | Yes / no | No | Manual validation gate |
| `phase3c11_2_provision_persistence_acl.php` | Persistence ACL | Role data | Update existing roles | Yes / no | No | Core candidate after schema gate |
| `phase3c17_provision_operational_centers_navigation.php` | Managed tab list with snapshot | Runtime config | Versioned/idempotent | Yes / no | Navigation restore possible | Core candidate; snapshot required |
| `phase3c17_provision_sales_development_command_center.php` | Command Center preferences | Preferences | Merge/update | Conditional / no | Local-test targeting | Refactor before core use |
| `phase3u04_provision_navbar_tab_order.php` | Deprecated compatibility wrapper | Delegates navigation | Delegated | No / no | No | Never direct; use C17 materializer |
| `phase_acl03_apply_sales_manager_field_visibility.php` | Sales-manager field visibility | Role field data | Update existing role | Conditional / no | No | Core candidate after field matrix approval |

## 8. Navigation and UI provisioning

The navigation definition is version-controlled and materialized through a single canonical migration. Browser editing is not an installation method.

Default information architecture proposal:

| Order | Entry | Visibility | Notes |
| ---:| --- | --- | --- |
| 1 | Accounts | ACL-governed | Native CRM |
| 2 | Contacts | ACL-governed | Native CRM |
| 3 | Leads | ACL-governed | Native CRM; no automatic creation |
| 4 | Opportunities | ACL-governed | Native CRM; no automatic creation |
| 5 | Prospect Pool | Prospecting operator/reviewer | Operational queue |
| 6 | Prospect Candidates | Reviewer/admin direct route, not necessarily primary tab | Internal candidate review |
| 7 | Prospect Runs | Prospecting operator/reviewer | Operational lifecycle view |
| 8 | Search Strategies | Prospecting operator/reviewer | Planning/management |
| 9 | Send Executions | Authorized monitoring roles | Lifecycle monitoring; no ungoverned transition |
| 10 | Outreach Center | Authorized outreach roles | Composite entry, not a provider action |
| 11 | Command Center | Authorized operators/admin | Dashboard/queue composition |
| 12 | Opportunity Candidates | Commercial reviewer/admin direct route | Candidate governance |
| 13 | Commercial Intelligence Workspace | Commercial reviewer/admin | Preferred entry from OpportunityCandidate; standalone tab only if usability validation proves need |

Internal audit entities, provider records, raw logs, and support-only artifacts must not be promoted to primary navigation.

Upgrade rules:

- Preserve non-governed user choices and native entries.
- Version only managed entries/dividers.
- Snapshot current navigation before a managed migration.
- Restore from the snapshot on failure.
- Validate the saved configuration after restart with an administrator and a restricted role.

## 9. Roles, teams, and ACL target model

| Role | Primary access | Explicit restrictions |
| --- | --- | --- |
| Administrator | Configuration, schema review, all approved staging entities | No provider credentials or production actions |
| Commercial workspace reviewer | Read governed candidates/workspace; approved review decisions only | No direct lifecycle bypass, no provider actions |
| Prospecting operator | Prospect pools, runs, search strategies, governed execution work | No automatic Lead/Opportunity creation, no provider egress |
| Read-only reviewer | Read approved lists/workspace | No create/edit/delete/lifecycle actions |
| System/integration identity | Only already-governed API boundaries | No interactive admin, provider, or unbounded write privileges |

Target authorization matrix:

| Role | Entity/field access | Lifecycle actions | Workspace/navigation | Provider and send execution | Administration |
| --- | --- | --- | --- | --- | --- |
| Administrator | Full staging read/write only for approved scopes; field visibility remains auditable | Approved guarded actions only | All managed entries | May inspect configuration; no credentials/provider egress; send monitoring only unless separately approved | Yes |
| Commercial workspace reviewer | Read OpportunityCandidate and Commercial Intelligence sources; write only reviewed decision artifacts | No transition bypass | Candidate route and Workspace | No provider access; no send mutation | No |
| Prospecting operator | Governed ProspectPool, ProspectRun, SearchStrategy, and approved queue fields | Only service-owned transitions exposed by approved UI | Prospecting entries, Command Center as assigned | No provider egress; SendExecution read/authorized workflow action only | No |
| Read-only reviewer | Read-only scope/field subset | None | Assigned lists/workspace only | No provider or send action | No |
| System/integration identity | Narrow API fields/scopes already governed by code | Only explicitly authorized integration save options | No interactive navigation | No provider credential management; no unbounded send action | No |

ACL provisioning must verify entity permissions, field visibility, lifecycle action gates, workspace visibility, and administrative boundaries by role. It must not expose usernames, passwords, API keys, or user preference contents.

Governance invariants retained by every migration:

- no automatic Lead creation;
- no automatic Opportunity creation;
- no unauthorized lifecycle transitions;
- no provider egress, runtime expansion, email sending, or outreach activation;
- no invariant activation beyond approved code;
- no production ownership or access changes.

## 10. Branding recovery and deployment

Branding recovery is a separate bounded work package. It must use a read-only helper process or targeted extraction against the local data volume, with an allowlist limited to:

- `applicationName`;
- theme identifier;
- logo and favicon references;
- approved labels and non-secret UI settings;
- exact approved logo/favicon/background/CSS files.

It must not export a full `data/config.php`, logs, sessions, customer uploads, provider settings, credentials, tokens, or database dumps.

For each recovered asset, record filename, MIME type, byte size, SHA-256, source category, destination, ownership, and fallback. Generic assets should become version-controlled branding assets. EspoCRM-uploaded files may remain in the data volume only when a stable file-ID reference is required.

Expected deployment controls:

- PNG/SVG/ICO/WebP only where supported by EspoCRM and browsers;
- explicit size limit established in DP-WP3;
- web-user-readable ownership;
- cache-busting filename or versioned reference;
- browser hard-refresh and login/navbar screenshot validation;
- approved Chitu fallback branding if recovery fails safely.

## 11. Database strategy

Create a fresh Railway staging schema from the base installation, canonical repository code, deterministic migrations, and approved safe defaults. The local database is reference evidence only and must not be wholesale imported.

Required schema checks:

```text
prospect_candidate                 prospect_run
search_strategy                    send_execution
research_evidence                  ai_qualification_insight
reply_signal                       opportunity_candidate
commercial_brief                   commercial_insight
business_review_context            decision_support_context
presentation_feedback              human_review_decision_record
numbering_sequence
```

Also verify core configuration tables/state required for roles, teams, preferences, extension registration, and scheduled-job definitions without importing historical schedules or logs.

Explicit exclusions:

- real customers, Leads, Contacts, Accounts, Opportunities, emails, and outreach history;
- credentials, API tokens, provider configuration, SMTP settings, and authentication secrets;
- personal user preferences;
- scheduled-job history, logs, sessions, caches, and temporary files;
- unreviewed uploads and historical extension backups.

Only separately approved synthetic records may be added after core bootstrap validates with an empty business-data set.

## 12. Data-volume policy

`/var/www/html/data` is the only persistent web volume.

| Classification | Contents | Handling |
| --- | --- | --- |
| Persist | Approved non-secret config, approved branding assets, staging uploads, required application state | Back up before migration; restore only from verified snapshot |
| Regenerate | Cache, compiled metadata, temporary files | Rebuild/clear after schema migrations |
| Do not migrate | Logs, sessions, local caches, secret-bearing exports, unreviewed uploads, extension backups, old installation artifacts | Exclude from release inputs |

First deployment creates an empty staging data volume. Upgrades retain it, take a snapshot before migration, and clear only generated cache. Volume replacement is a last-resort recovery action requiring a verified DB/config backup and explicit authorization.

## 13. Entrypoint, release runner, and failure handling

The long-running Apache container must only prepare safe runtime state and start Apache. It must not re-run migrations, seed users, delete records, or mutate navigation on every restart.

Preferred implementation shape:

| Operation | Mechanism |
| --- | --- |
| Image build | Canonical overlay, manifest verification, executable release tooling |
| Normal web startup | Port/Apache setup, overlay verification, non-destructive cache handling, Apache exec |
| Schema/config migration | One-shot Railway release command or dedicated migration service |
| Bootstrap validation | Release job after migration, before declaring deployment healthy |
| Synthetic fixtures | Explicit staging-only command under separate authorization |

The runner requires a database advisory lock, migration timeout, single-writer behavior, redacted logs, bounded retries for transient database readiness, and a failed-ledger recovery procedure. A failed migration blocks further automatic advancement until an operator reviews the preserved backup and ledger state.

## 14. Testing and validation plan

### Automated/static tests

- canonical package/overlay manifest parity;
- manifest version, Git commit, ZIP completeness, and stale-artifact rejection;
- required backend/frontend file presence;
- installer/migration-ledger contract;
- navigation definition and provisioning inventory;
- branding allowlist validation;
- provisioning classification: core, staging-only, never automatic.

### Container tests

- image build, Apache MPM selection, syntax, PHP syntax, and app check;
- writable data volume and immutable image overlay;
- fresh MySQL bootstrap;
- migration dry-run and successful first run;
- second-run idempotency;
- restart persistence for config, branding, modules, and navigation;
- lock contention and partial-migration recovery.

### Database tests

- all required C16–C25 tables and key schema columns;
- `numbering_sequence` existence and safe initialization;
- extension version and successful ledger rows;
- roles, teams, ACL maps, navigation, and dashboards;
- absence of provider credentials and business data;
- no historical user preferences or scheduled-job logs imported.

### Browser tests

- branded login, browser title, and navbar;
- Accounts, Contacts, Leads, Opportunities;
- Prospect Candidate, Prospect Run, Search Strategy, Send Execution, Opportunity Candidate;
- Commercial Intelligence Workspace with controlled no-anchor state;
- role-based access denial/visibility behavior;
- browser console and network-error review;
- hard refresh and service-restart persistence.

### Boundary tests

- no automatic Lead or Opportunity creation;
- no provider egress, email sending, or outreach activation;
- no lifecycle mutation on page load;
- no unauthorized write action;
- no production promotion path.

Stage B browser validation begins only after all automated, container, schema, and configuration gates pass.

## 15. Implementation work packages

| WP | Objective | Authorized files/output | Preconditions | Tests/exit criteria | Separate authorization |
| --- | --- | --- | --- | --- | --- |
| DP-WP0 | Deployment contract and artifact manifest | Deployment docs, release manifest tests | Ratified plan | One canonical source/version/hash definition | Yes |
| DP-WP1 | Deterministic extension installation | Docker/release runner/migration ledger | DP-WP0 | Fresh install and second-run pass | Yes |
| DP-WP2 | Configuration provisioning | Reviewed role/team/ACL/nav/dashboard definitions | DP-WP1 | Idempotent staging defaults, no fixture data | Yes |
| DP-WP3 | Branding migration | Allowlisted recovery tooling/assets/config | DP-WP0 | Safe extraction, hash, visual validation | Yes |
| DP-WP4 | Fresh DB bootstrap | Schema tests and synthetic-data policy | DP-WP1/2 | Required tables, no business data | Yes |
| DP-WP5 | Railway integration | Release command, locking, health/backup controls | DP-WP1–4 | Deploy/restart/rollback rehearsal | Yes |
| DP-WP6 | Automated validation | Static, container, DB, and browser harnesses | DP-WP1–5 | All gates pass | Yes |
| DP-WP7 | Staging deployment and review | Railway deployment evidence and Stage B report | DP-WP6 | Independent browser review and closure | Yes |

Every package must define a bounded rollback, prohibited scope, and file list before work begins. No package authorizes unrelated connector, scoring, research, email-generation, provider, or production work.

### Work-package delivery contracts

| WP | Outputs and authorized implementation area | Rollback | Prohibited scope |
| --- | --- | --- | --- |
| DP-WP0 | Release manifest, artifact contract, stale-ZIP disposition, tests; deployment documentation and release tooling only | Revert manifest/tooling change | Docker/Railway/database mutation |
| DP-WP1 | Versioned migration runner, ledger, reviewed install-hook equivalent, rebuild contract | Ledger-aware compensating migration or staging snapshot restore | Roles, branding, fixture data, provider activation |
| DP-WP2 | Approved role/team/ACL/navigation/dashboard definitions and tests | Config/navigation snapshot restore | Test users, business data, personal preferences, credential changes |
| DP-WP3 | Read-only allowlisted asset recovery, branding manifest, approved assets/defaults | Revert asset references to approved fallback | Full config export, customer uploads, logo creation without approval |
| DP-WP4 | Fresh-bootstrap schema tests and synthetic-data policy | Disposable staging DB/volume restore only | Local DB import, real business records |
| DP-WP5 | Railway release-runner integration, locks, health/backup controls | Redeploy prior compatible image and restore verified snapshot | Production changes, deletion of MySQL/volume |
| DP-WP6 | Automated static/container/database/browser test harnesses | Revert test-only artifacts | Live provider, outreach, or production testing |
| DP-WP7 | Authorized staging deployment evidence and independent browser review | Use the pre-deploy rollback checkpoints | Manual browser configuration as a substitute for migrations |

Each package's authorization request must name its exact files, migration IDs, test commands, expected state changes, and exit criteria. A package may not start until its dependency row has passed review.

## 16. Rollback plan

Prepare these rollback points before any migration:

| Layer | Rollback artifact | Failure response |
| --- | --- | --- |
| Git/image | Prior commit and successful image digest | Redeploy prior image only after DB compatibility check |
| Migration | Ledger row plus migration snapshot | Stop advancement; run reviewed recovery/restore path |
| MySQL | Verified staging snapshot | Restore only with explicit authorization |
| Data volume | Verified volume/config snapshot | Restore approved config/assets; do not delete blindly |
| Navigation | Versioned pre-migration snapshot | Restore managed tab list |
| Branding | Asset manifest/checksums | Revert references/assets to approved fallback |

| Failure | Required response |
| --- | --- |
| Image starts, migration fails | Mark ledger failed, block release, preserve snapshots, do not retry blindly |
| Migration succeeds, provisioning fails | Stop before browser validation; restore configuration snapshot or run versioned compensating migration |
| Branding fails | Use approved fallback; do not silently retain stock branding as a pass condition |
| Browser validation fails | Preserve deployment evidence; remediate in a new work package |
| Restart persistence fails | Treat as release failure; inspect volume/migration boundaries before retry |
| Healthcheck fails | Keep DB/volume intact; diagnose image and release logs without destructive actions |

Never delete the Railway MySQL service or data volume without a verified backup and explicit authorization.

## 17. Security boundaries

| Artifact/category | Classification | Rule |
| --- | --- | --- |
| Extension code, navigation definitions, migration code | Source-controlled | No secrets or business data |
| Branding manifest and approved generic assets | Internal configuration/source-controlled after approval | Hash and review |
| Application non-secret defaults | Internal configuration | Separate from secret variables |
| Railway DB/admin credentials, tokens, SMTP/provider settings | Secret | Railway variables only; never logs/Git/docs |
| Local config exports, uploads, DB rows, screenshots with records | Personal/business data | Allowlisted, redacted, minimally retained |
| Cache, logs, sessions, generated metadata | Generated | Never migration source |

Prohibited throughout implementation: full `data/config.php` export, database dumps in Git, provider credentials, production data, authentication cookies, unsafe screenshots, and activation of email/provider/outreach behavior.

## 18. Acceptance criteria

The deployment is successful only when all conditions hold:

1. Railway builds the authorized repository commit and canonical release manifest.
2. EspoCRM starts, remains healthy, and uses dedicated staging MySQL.
3. Required C16–C25 tables, extension state, and successful migrations are recorded.
4. Roles, teams, ACL, navigation, dashboards, and staging defaults are deterministic.
5. Approved Chitu branding is visible; stock appearance is not accepted as parity.
6. Principal custom routes load and the C25 workspace has a valid controlled state.
7. No provider egress, email sending, automatic Lead/Opportunity creation, or unauthorized lifecycle mutation occurs.
8. Restart preserves application configuration, navigation, and branding.
9. A new fresh staging deployment reproduces the same result.
10. Automated validation and independent Stage B browser review pass.
11. Production promotion remains separately unauthorized.

## 19. Authorization gates

| Gate | Required decision |
| --- | --- |
| Plan ratification | Approve this plan and the independent review before implementation |
| DP-WP0 through DP-WP7 | Authorize each bounded package separately |
| Branding recovery | Explicit approval for allowlisted local-volume inspection |
| Railway deployment | Authorize only after implementation tests pass |
| Stage B | Authorize after release gates pass |
| Production promotion | Separate future authorization only |

## 20. Evidence to retain

- release manifest and image digest;
- migration ledger export with redacted failures only;
- database table/ACL/navigation assertion results;
- volume/config/branding snapshot identifiers and checksums;
- automated test reports;
- browser screenshots and console/network summary without credentials or personal data;
- rollback rehearsal result.

This plan is ratified as an architectural and work-package governance record. It does not authorize execution; implementation begins only after separate authorization of DP-WP0.
