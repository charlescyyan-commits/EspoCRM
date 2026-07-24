# Phase3C17 WP1.4B Navigation Runtime Fix Report

## Scope

This change repairs implementation gaps found by the Phase3C17 browser-smoke
investigation. It does not alter the C17 navigation authority, `tabList`,
workflow ownership, ACL, entity metadata, or database schema.

## Root cause and repair

### Outreach Center (`DraftApproval`)

The EspoCRM runtime log recorded repeated requests to `GET /DraftApproval`
failing with:

```text
Controller 'DraftApproval' does not exist.
```

`DraftApproval` already had an entity definition, scope, client definition,
layouts, and a `#DraftApproval` operational-center entry. Unlike the working
Quote record surface, it lacked the module's native `Record` controller.

Added `Controllers/DraftApproval.php`, matching the existing
`Controllers/Quote.php` pattern. The controller supplies EspoCRM's standard
record API for the existing DraftApproval entity; it adds no action, workflow,
ACL, or entity behavior.

### Quote Center

Historical runtime logs also contain `Controller 'Quote' does not exist`
entries from before the Quote controller was packaged. The current source and
installed `1.9.8-alpha` runtime both contain `Controllers/Quote.php`.
The new canonical package retains that controller and adds a focused contract
test requiring both operational record controllers. No Quote workflow service,
route, status transition, or authorization rule changed.

## Localization completion

Visible fixed English strings are now backed by matching `en_US` and `zh_CN`
labels for:

- Search Center navigation, form labels, helper text, and result messages.
- Prospecting Operations dashboard navigation, workflow guidance, summaries,
  empty states, recent-activity table, and metrics.
- Quote workflow action labels, confirmations, success messages, and fallback
  error text.

The existing client-side routes and server action endpoints remain unchanged.

## Release artifact

Source bytes changed, so the frozen `1.9.8-alpha` artifact was preserved and a
new canonical development artifact was promoted:

| Item | Value |
| --- | --- |
| Version | `1.9.9-alpha` |
| Artifact | `deployment/prospecting-extension-1.9.9-alpha.zip` |
| SHA-256 | `CDCD1130C781AEEC92AC08F298DB5355E4F1520274FDE90EB3BAF32ED2292A47` |

`python crm-extension/scripts/build_release_package.py --check` verified exact
source-to-artifact byte parity and the committed SHA-256 sidecar.

## Validation

| Check | Result |
| --- | --- |
| WP1.4B + existing navigation/UI focused tests | PASS — 32 passed |
| Extension suite | PASS — 236 passed, 22 subtests passed |
| Release integrity and package consumers | PASS — 26 passed, 336 subtests passed |
| Artifact build and `--check` | PASS |
| PHP lint in local container | Not run — container command authorization was denied by the environment quota |
| Browser smoke on `http://localhost:8090` | Not run — browser security policy rejected the local URL |
| Local container deployment/rebuild | Not run — container command authorization was denied by the environment quota |

## Remaining runtime verification

Install `prospecting-extension-1.9.9-alpha.zip` into the disposable EspoCRM
10.0.1 runtime, clear/rebuild metadata through the normal deployment process,
then verify an authenticated user can open `#DraftApproval` and `#Quote`.
The required browser smoke could not be run in this environment because the
browser policy disallowed the requested local runtime URL; no authentication or
browser-policy workaround was attempted.
