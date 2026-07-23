# Phase3C17 WP0.5 Metadata Source Convergence Guard Implementation

**Status:** IMPLEMENTED
**Date:** 2026-07-23
**Baseline:** Phase3C17 WP0.4b externalized workflow authorization bindings (`0cf57d7`)

---

## 1. Change Summary

Implemented the Phase3C17 metadata source convergence guard. Three coordinated commits remove the stale `crm-extension/Resources/` and `crm-extension/custom/` duplicate metadata trees and install an offline guard that enforces a single authoritative Prospecting metadata source tree:

- `6920719` — add metadata source convergence guard (guard test + stale-tree marker)
- `b937cf1` — physically remove 67 stale files from `crm-extension/Resources/` and 4 READMEs from the `crm-extension/custom/` placeholder tree
- `51cce6d` — extend the guard to also reject the `crm-extension/custom/` placeholder tree

The guard ensures that the duplication reported and closed in `docs/architecture/EXTENSION_SINGLE_SOURCE_MIGRATION_REPORT.md` (2026-07-11) cannot silently re-enter the repository. No product code was changed; the guard is an offline test-only artifact.

## 2. Files Changed

| File | Action | Description |
|------|--------|-------------|
| `crm-extension/tests/test_phase3c17_wp0_5_metadata_source_guard.py` | **Created** (44→51 lines) | Offline guard validating: authoritative tree exists, stale `Resources/` absent, no unpackaged `Resources` trees elsewhere, legacy `custom/` placeholder absent |
| `crm-extension/Resources/` (67 files) | **Deleted** | Stale duplicate of `files/custom/Espo/Modules/Prospecting/Resources/` — entityDefs, acl, layouts, formula, routes, READMEs |
| `crm-extension/custom/Espo/Modules/Prospecting/Api/README.md` | **Deleted** | Non-packaged placeholder README |
| `crm-extension/custom/Espo/Modules/Prospecting/Controllers/README.md` | **Deleted** | Non-packaged placeholder README |
| `crm-extension/custom/Espo/Modules/Prospecting/README.md` | **Deleted** | Non-packaged placeholder README |
| `crm-extension/custom/Espo/Modules/Prospecting/Services/README.md` | **Deleted** | Non-packaged placeholder README |
| `crm-extension/tests/test_c16_entity_contracts.py` | **Modified** | Removed stale-Resources assertion (guard test now owns this) |
| `crm-extension/tests/test_extension_skeleton.py` | **Modified** | Removed stale-Resources file count expectation |
| `crm-extension/tests/test_phase3c02_search_strategy_foundation.py` | **Modified** | Removed stale-Resources assertion |
| `docs/architecture/DIRECTORY_STRUCTURE.md` | **Modified** | Updated directory structure documentation |

## 3. Architecture: Single Canonical Metadata Source

```
crm-extension/files/custom/Espo/Modules/Prospecting/Resources/
├── i18n/          (en_US, zh_CN)
├── layouts/
├── metadata/
│   ├── aclDefs/
│   ├── app/
│   ├── clientDefs/
│   ├── dashlets/
│   ├── entityDefs/
│   ├── formula/
│   ├── scopes/
│   └── selectDefs/
├── module.json
└── routes.json
```

This is the **single authoritative installable metadata source** (`crm-extension/README.md:14-32`). The former duplicate overlay at `crm-extension/Resources/` and the non-packaged placeholder tree at `crm-extension/custom/` have been permanently removed.

### Guard Coverage (4 assertions)

| Assertion | Coverage |
|-----------|----------|
| `test_packaged_prospecting_resources_are_authoritative` | Confirms `files/custom/Espo/Modules/Prospecting/Resources/` exists with `metadata/`, `layouts/`, `i18n/` subdirectories |
| `test_stale_metadata_tree_has_been_removed` | Confirms `crm-extension/Resources/` does not exist |
| `test_no_unpackaged_prospecting_resources_tree_exists` | Confirms no `Resources/` directory exists anywhere under `crm-extension/` outside the packaged `files/` tree |
| `test_legacy_custom_placeholder_tree_has_been_removed` | Confirms `crm-extension/custom/` does not exist |

## 4. Strict Restrictions Compliance

| Restriction | Status |
|-------------|--------|
| Do not modify product code | ✅ Zero product-code changes; guard is test-only |
| Do not modify entity definitions | ✅ No entityDefs changed |
| Do not modify ACL definitions | ✅ No aclDefs changed |
| Do not modify layouts | ✅ No layouts changed |
| Do not remove any file from the installable tree | ✅ Only stale duplicates and placeholder READMEs removed |
| Do not break downstream test suites | ✅ All existing tests updated to remove stale-Resources assertions |

## 5. Test Results

```text
python -m unittest crm-extension.tests.test_phase3c17_wp0_5_metadata_source_guard -v
# Ran 4 tests — OK

python -m unittest discover -s crm-extension/tests -p test_*.py
# Ran tests — OK (all suites updated for removed stale trees)
```

**Test coverage:**
- Authoritative metadata tree presence (3 required subdirectories)
- Stale `crm-extension/Resources/` absence
- No unpackaged `Resources/` trees outside the packaged root
- Legacy `crm-extension/custom/` placeholder absence
- Guard is self-verifying: if the stale trees are recreated, the test fails at the next gate run

## 6. Risk Assessment

**Low risk.** This change:

- Removes only duplicated files whose authoritative copies are verified present in `files/custom/Espo/Modules/Prospecting/Resources/`
- Removes 4 README placeholders from a non-packaged `custom/` tree
- Adds one offline guard test — no runtime behavior change
- Updates 3 existing tests to remove stale-Resources assertions (they no longer need to validate a tree that shouldn't exist)
- All product code, metadata, routes, and service files under `files/` are untouched

## 7. Pre-existing Architecture Used

- Single canonical source tree established by `EXTENSION_SINGLE_SOURCE_MIGRATION_REPORT.md` (2026-07-11)
- Parity tests at `crm-extension/tests/test_c16_entity_contracts.py` guard the `crm-extension/Resources/` design mirror (separate concern from this guard)
- ZIP builder at `crm-extension/scripts/build_release_package.py` packages only `files/` — stale duplicates were never in the release artifact
