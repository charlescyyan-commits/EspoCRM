# Railway DP-WP1 Deterministic Extension Installation Charter Review

| Field | Value |
| --- | --- |
| Review status | PASS — DP-WP1 CHARTER READY FOR AUTHORIZATION |
| Reviewed charter | `docs/deployment/RAILWAY_DP_WP1_INSTALLATION_CHARTER.md` |
| Repository baseline reviewed | `8ede18ebd26984b516eefac4f6c8facb32068f01` |
| DP-WP0 prerequisite | RATIFIED AND COMMITTED |
| Implementation authority | Not granted by this review |

## 1. Review Scope

This is an independent governance review of the DP-WP1 charter only. It reviews the proposed deterministic installation boundary; it does not run an installer, execute the extension hook, connect to Railway or MySQL, modify runtime state, or authorize implementation.

## 2. DP-WP0 Alignment

**PASS.** The charter consumes the DP-WP0 manifest as the sole release-artifact verification input, preserves extension identity from `crm-extension/manifest.json`, and keeps the immutable release identity intact. It does not revise canonical roots, manifest generation, artifact hashes, or source-of-truth exclusions. It expressly rejects local Docker code volumes and local/Railway databases as installation sources.

## 3. Installation Boundary

**PASS.** The charter correctly distinguishes an operational EspoCRM base image from a verified installed Chitu application state. Its model requires a verified overlay, explicit administrative runner, lock, ledger, and postcondition validation. It bars volume-copying, undocumented configuration changes, manual browser setup as the primary mechanism, and startup-triggered installation.

## 4. `AfterInstall.php` Classification

**PASS.** The review confirms that the current hook performs extension-owned `numbering_sequence` table initialization and `DataManager::rebuild()`. The charter does not permit opaque or automatic hook execution. It conditions the table operation on a named, versioned, locked, ledgered step and conditions metadata rebuild on verified artifacts and successful database steps. No external API, credential, email, business-data, or autonomous lifecycle action is present in the reviewed hook; the charter forbids all of them nonetheless.

## 5. Migration and Ledger Contract

**PASS.** The charter confines DP-WP1 to installation-runner mechanics and reserves complete C16–C25 schema/migration implementation for DP-WP4. It requires stable step IDs, ordering, checksums, a held lock, durable outcomes, and postconditions. Its ledger includes all required identity and outcome fields: installation ID, extension name/version, artifact-manifest hash, source commit, completion time, status, executed steps, and redacted failure reason.

## 6. Restart, Failure, and Rollback Safety

**PASS.** The charter requires incomplete-state discovery, identity-matching resume, postcondition revalidation, duplicate-step prevention, mismatch blocking, and explicit failure records. Rollback is limited to installation state and reviewed non-destructive compensation; it does not imply database restoration, production action, full deployment rollback, or data import.

## 7. Security and Scope-Creep Controls

**PASS.** Credentials, provider activity, business data, email, external calls, autonomous workflows, browser validation, provisioning, branding, Railway integration, and downstream deployment closure are outside the installation path. The charter assigns each of these concerns to its appropriate work package or to separate authorization.

## 8. Downstream Ownership

**PASS.** The ownership table preserves DP-WP0's contract role and clearly separates DP-WP1 from DP-WP2 provisioning, DP-WP3 branding, DP-WP4 schema work, DP-WP5 Railway integration, DP-WP6 validation, and DP-WP7 closure. No downstream package is implicitly authorized.

## 9. Findings

No unresolved findings were identified in the charter. The observed direct DDL and metadata rebuild in `AfterInstall.php` are expressly converted into future implementation acceptance requirements; this review does not accept direct execution of the hook as an implementation mechanism.

## 10. Verdict and Authorization State

**PASS — DP-WP1 CHARTER READY FOR AUTHORIZATION**

The charter is sufficient to govern a separately authorized DP-WP1 implementation. This verdict is not implementation authorization and is not evidence that any installation action occurred.

| Work package | State |
| --- | --- |
| DP-WP0 | RATIFIED AND COMMITTED |
| DP-WP1 | ELIGIBLE — NOT AUTHORIZED |
| DP-WP2–DP-WP7 | NOT AUTHORIZED |
