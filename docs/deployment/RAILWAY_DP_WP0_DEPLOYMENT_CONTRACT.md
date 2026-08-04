# Railway DP-WP0 Deployment Contract

| Field | Value |
| --- | --- |
| Status | IMPLEMENTED CONTRACT — RATIFICATION STATUS RECORDED EXTERNALLY |
| Work package | DP-WP0 — Deployment Contract and Artifact Manifest |
| Authorized source baseline | `6ef712134f581a12a18da5c98691884e73388b78` |
| Deployment model | Model B — deterministic repository overlay |
| Manifest | `deployment/railway/full-application-artifact-manifest.json` |
| Independent review (authoritative review evidence) | `docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_REVIEW.md` |
| Ratification record (authoritative governance status) | `docs/audit/RAILWAY_DP_WP0_DEPLOYMENT_CONTRACT_RATIFICATION.md` |

```text
This contract is technically immutable after DP-WP0 implementation for
manifest integrity. Ratification and amendment outcomes are recorded only
in the external ratification record. Changing ratification status must not
require rewriting this contract's bytes.
```

## 1. Purpose

This contract defines a deterministic, machine-verifiable inventory for the complete C16–C25 Railway staging release. It identifies release inputs, their SHA-256 hashes, release identity, candidate-only configuration inputs, and content that later work packages must not treat as release source.

It is an inventory and verification contract. It does not build an image, execute an installation hook, migrate a database, provision configuration, deploy to Railway, or mutate application runtime state.

## 2. Ratified Governance Basis

This contract implements the bounded DP-WP0 output required by:

- `docs/deployment/RAILWAY_FULL_APPLICATION_DEPLOYMENT_PLAN.md`;
- `docs/audit/RAILWAY_FULL_APPLICATION_DEPLOYMENT_PLAN_REVIEW.md`;
- `docs/audit/RAILWAY_FULL_APPLICATION_DEPLOYMENT_PLAN_RATIFICATION.md`.

The ratified plan remains `RATIFIED — IMPLEMENTATION REQUIRES SEPARATE DP-WP AUTHORIZATION`. DP-WP0 implementation of this contract is complete; ratification status is recorded externally and remains separately governed. DP-WP1 through DP-WP7 remain separately unauthorized.

## 3. Deployment Model

Model B uses the repository’s canonical code overlay with a future explicit, locked migration runner and durable ledger. This contract supplies the file-level release identity that DP-WP1 must consume; it neither implements nor invokes that runner.

## 4. Canonical Sources

| Source | Classification | Manifest treatment |
| --- | --- | --- |
| `crm-extension/files/custom` | Canonical backend deployment artifact | Every regular file is hashed as required `application-code`. |
| `crm-extension/files/client/custom` | Canonical frontend deployment artifact | Every regular file is hashed as required `application-code`. |
| `crm-extension/manifest.json` | Canonical release identity | Parsed for extension name/version and hashed. |
| `crm-extension/scripts/AfterInstall.php` | Required reviewed installation input | Hashed and required; never executed by DP-WP0. |
| `deployment/provisioning/**` | Candidate input | Hashed as optional `provisioning-candidate`; no execution authority. |
| `deployment/navigation/**` | Candidate input | Hashed as optional `navigation-candidate`; no execution authority. |
| Railway Dockerfile, entrypoint, healthcheck, and `railway.toml` | Required infrastructure inputs | Hashed as required `railway-infrastructure`; not modified or executed. |
| This contract, generator, and focused test | Contract-verification inputs | Hashed to make contract evidence reproducible; not runtime artifacts. |

The required-artifact list includes the three module descriptors and representative AIPlatform, Prospecting, C20–C24, C25, Workspace controller/view/template/routes, ACL, and Railway input paths discovered in the repository. The generator fails before writing when any required item is absent.

## 5. Non-Canonical Sources

| Source | Classification | Rule |
| --- | --- | --- |
| Local Docker code volumes | Non-canonical reference only | Never copy into repository code or image overlay. |
| Local MySQL and Railway MySQL | Runtime/reference state | Never a release artifact or import source. |
| `/var/www/html/data` | Runtime state | Not included in the release manifest. |
| Branding assets | DP-WP3-owned | Excluded until explicitly recovered, allowlisted, and approved. |
| Provider credentials, customer/business data, uploads, preferences | Forbidden | Never include in manifest or release source. |
| Generated caches, logs, sessions, and screenshots | Forbidden/generated | Never include in manifest. |

## 6. Release Identity

The generator parses `extensionName` and `version` directly from `crm-extension/manifest.json`; it does not duplicate the version manually. The DP-WP0 release identity records schema version `1`, deployment model `deterministic-overlay`, and:

```text
release.gitCommit = authorized source baseline used to generate the DP-WP0 artifact set
                 = 6ef712134f581a12a18da5c98691884e73388b78
```

That value is the authorized source baseline for this artifact set. It is not the future closure commit that may later contain the generated manifest, and it must not be rewritten to embed the manifest's own containing Git commit (that would create a self-reference cycle). A new authorized baseline requires separate authorization and a deliberate contract/manifest update.

## 7. Artifact Manifest Schema

The JSON document has deterministic key order, two-space indentation, UTF-8 encoding, and a trailing newline. It contains:

```text
schemaVersion
release { extensionName, extensionVersion, gitCommit, deploymentModel }
canonicalRoots
requiredArtifacts
files { path, sha256, bytes, category, sourceRoot, required, executionStatus }
excludedPatterns
forbiddenPatterns
legacyArtifacts
executionBoundary
```

All file paths are repository-relative POSIX paths, case-preserving, traversal-free, unique, and sorted lexicographically. No timestamp, user name, machine path, container identifier, or Railway deployment identifier is emitted.

## 8. Required Artifacts

The required-artifact list is intentionally representative as well as structural:

- extension manifest and reviewed install hook;
- AIPlatform, Prospecting, and CommercialIntelligence module descriptors;
- AI platform metadata and C20–C25 entity metadata: ProspectCandidate, ProspectRun, SearchStrategy, ResearchEvidence, AIQualificationInsight, SendExecution, ReplySignal, OpportunityCandidate, CommercialBrief, CommercialInsight, BusinessReviewContext, DecisionSupportContext, PresentationFeedback, and HumanReviewDecisionRecord;
- Commercial Intelligence Workspace controller, view, template, and routes;
- Prospecting and AIPlatform ACL definitions;
- Railway Dockerfile, entrypoint, healthcheck, and configuration.

Presence in this inventory means only that a path is part of the verified contract. It never authorizes a hook, a candidate provisioning script, a navigation definition, or a runtime action.

## 9. Exclusions and Forbidden Content

The contract excludes Git metadata, Python/test caches, generated caches/logs/sessions, temporary/editor/OS files, screenshots, and local comparison output. Mutable governance-status records are also excluded from the canonical hashed inventory, including ratification records, amendment-status appendices, and temporary audit evidence. Those files may document governance outcomes but are not deployment inputs.

It forbids environment files, private key/certificate formats, database dumps/exports, data configuration, internal configuration, uploads, cookies, and sessions.

The generator applies focused path-based checks to the allowlisted artifact set. It deliberately does not perform broad source-text secret scanning, which would confuse safe identifiers with credentials. Review validation additionally uses narrow assignment-pattern checks.

## 10. Legacy ZIP Disposition

`deployment/prospecting-extension-1.9.13-alpha.zip` has SHA-256 `785affd89f1fcea8372faf3eb2a37e2ae3730169e51aadb4eb02c75f68d96c5a`, 461 file entries, and embedded version `1.9.13-alpha`. Its embedded manifest and install hook happen to match the current copies, but it lacks 153 canonical code files, has no C25 Commercial Intelligence content, and therefore cannot represent the complete application. The generated manifest retains the exact missing/extra path comparison (`153` missing and `0` extra code paths at this baseline).

Its fixed disposition is **LEGACY — NOT A DEPLOYMENT SOURCE**. It is not a canonical file entry, is never copied by the generator, and is not deleted or regenerated here. Only a separately authorized DP-WP1 may decide whether to create a new package from a regenerated, verified manifest.

## 11. Generator Contract

Run from repository root:

```powershell
python scripts/generate_railway_artifact_manifest.py
python scripts/generate_railway_artifact_manifest.py --check
```

Generate mode writes atomically: a temporary file is written beside the target and atomically replaced. Check mode reads only and fails if the generated bytes differ from the checked-in manifest. The generator uses Python’s standard library, has no network, Docker, Railway, database, or Git-mutation dependency.

It fails clearly for missing required sources, duplicate or unsafe paths, symlinks, forbidden artifacts, invalid extension identity, unavailable Git identity, unsafe output paths, unreadable legacy ZIPs, and stale/missing `--check` output.

## 12. Verification Contract

The focused test suite verifies deterministic rendering, check mode, schema shape, sorted/unique normalized paths, hashes for all entries, required C20–C25 artifacts, release identity, forbidden-path exclusion, stale-ZIP isolation, local-runtime exclusion, candidate execution boundaries, missing-file failure, and path-traversal/symlink rejection.

DP-WP0 exit requires generator success, check-mode success, JSON parsing, focused tests, a clean diff check, and independent review. It does not require or permit deployment validation.

## 13. Downstream DP-WP Responsibilities

| Work package | Consumes or owns |
| --- | --- |
| DP-WP1 | Consumes manifest for deterministic extension installation, migration runner, and ledger. |
| DP-WP2 | Classifies and implements reviewed provisioning, roles, ACL, navigation, and dashboards. |
| DP-WP3 | Owns branding recovery, allowlisting, and branding manifest. |
| DP-WP4 | Owns fresh database bootstrap and synthetic-data policy. |
| DP-WP5 | Owns Railway integration, release command, locks, health, and backups. |
| DP-WP6 | Owns broader automated/container/database/browser validation. |
| DP-WP7 | Owns staging deployment evidence, independent review, and closure. |

## 14. Authorization Boundary

DP-WP0 does not authorize execution of `AfterInstall.php`, migrations, provisioning, deployment, branding recovery, database mutation, browser validation, provider integration, runtime expansion, invariant activation, or production promotion.

## 15. Exit Criteria

- The generated manifest has deterministic hashes and full release identity.
- Required artifacts exist and candidate inputs are marked non-executable.
- The historic ZIP is isolated as legacy.
- Focused tests and JSON/check-mode validation pass.
- The independent review finds the contract ready for DP-WP0 ratification or records any required amendment.

## 16. Rollback

DP-WP0 rollback is repository-file rollback only. It has no database, volume, Railway, Docker, application-runtime, or provider side effect.

## 17. Open Informational Items

- The historic ZIP release-gating item is addressed by explicit legacy isolation; any new package remains a DP-WP1 decision.
- Navigation candidate selection remains DP-WP2-owned.
- Branding discovery and approval remain DP-WP3-owned.
