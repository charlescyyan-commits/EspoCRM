# Phase U04 - Prospecting Navigation Polish Report

**Date:** 2026-07-14

**Result:** **PASS WITH CONDITIONS**

## Native navigation decision

The local runtime is EspoCRM `10.0.1`. Its native `config.tabList` supports
scope entries and `divider` entries; it does not support an arbitrary nested
left-navigation tree without custom client code. The implemented native
equivalent is therefore one `Prospecting` divider with these entries directly
beneath it:

```text
Prospecting
  Search
  Search Jobs
  Prospect Pool
  Research Center
```

This preserves the requested information hierarchy without React, a custom SPA,
or a custom navigation view.

## Changes

| File | Change | Scope confirmation |
|---|---|---|
| `deployment/provisioning/phase3u04_provision_navbar_tab_order.php` | Uses the native `tabList` and an idempotent `Prospecting` divider; keeps only the four requested Prospecting entries; removes `Meeting`, `Call`, `Case`, `Ticket`, `ProspectingDashboard`, and `SearchStrategy` from the global tab list. | Navigation/menu only. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json` | Renames the `ResearchEvidence` navigation label to `Research Center`. | Label only. |
| `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/zh_CN/Global.json` | Renames the `ResearchEvidence` navigation label to `研究中心`. | Label only. |

No entity definition, scope, ACL, backend service, connector, dashboard layout,
or JavaScript source was changed. `ProspectingDashboard` remains a dashboard
surface; it is only removed from the navigation tab list.

## Runtime navigation verification

The provisioning script was copied to the local `espocrm` container, passed
`php -l`, and was executed twice. The second execution completed normally,
proving the divider-removal logic is idempotent for both legacy object and
current array divider representations.

The effective runtime `config.tabList` ends with exactly:

```text
DIVIDER: Prospecting (id: phase3u04-prospecting)
ProspectingSearch
SearchJob
ProspectPool
ResearchEvidence
```

`Meeting`, `Call`, `Case`, `Ticket`, `ProspectingDashboard`, and
`SearchStrategy` are absent from the effective `tabList`.

## Access-control verification

No ACL was changed. A read-only runtime role inventory confirmed:

| User type | Relevant effective role access | Result |
|---|---|---|
| Admin | all access to `SearchStrategy`, `SearchJob`, `ProspectPool`, and `ResearchEvidence` | The four navigation entries remain available. |
| Sales User | own create/read/edit for `SearchStrategy`, `SearchJob`, and `ProspectPool`; own read and no create/edit for `ResearchEvidence` | Native ACL continues to limit list and record access; adding a tab cannot elevate permissions. |

The four scopes retain their existing Prospecting ACL declarations. The native
navbar filters scope tabs by access, so this navigation-only change introduces
no permission grant.

## Validation

| Check | Result |
|---|---|
| English and Chinese Global JSON parse | PASS |
| Provisioning PHP syntax in runtime | PASS |
| Provisioning idempotency (two executions) | PASS |
| Runtime `tabList` exact target membership | PASS |
| Existing Prospecting menu/empty-state tests | PASS - 5/5 |
| JavaScript change introduced | PASS - no `.js` file changed |
| Admin browser menu render | DEFERRED |
| Sales User browser menu render | DEFERRED |
| Browser console error observation | DEFERRED |

The browser checks are deferred because no authenticated browser session was
available in this task. In addition, the installed runtime language files still
contain `Research Evidence` / `AI 研究证据`; the new source labels have not been
loaded into runtime metadata. No rebuild or cache operation was performed as
part of this navigation-only change.

## Conditions and next step

1. Deploy the two updated language metadata files through the normal extension
   release path, then perform the approved metadata refresh.
2. In an authenticated browser, sign in once as Admin and once as Sales User;
   verify the divider and four labels, the absence of the three hidden modules,
   a Sales User `ResearchEvidence` list restricted to own records, and an empty
   browser console.

The navigation configuration itself is active and verified. The only remaining
condition for an unconditional PASS is the post-deployment browser label and
console smoke check. No commit was created.
