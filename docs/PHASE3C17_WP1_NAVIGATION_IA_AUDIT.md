# Phase3C17 WP1 — Navigation IA Audit

**Status:** Accepted governance record

## Decision

The accepted C17 navigation model has one global `config.tabList` writer:

```text
ADR_C17_NAVIGATION_OPERATIONAL_CENTERS
  -> deployment/navigation/phase3c17_navigation.json
  -> phase3c17_provision_operational_centers_navigation.php
  -> config.tabList
```

`phase3u04_provision_navbar_tab_order.php` remains a compatibility wrapper only.
The accepted ADR is authoritative if a historical report conflicts with it.

## Frozen Information Architecture

| Class | Placement | Rule |
| --- | --- | --- |
| A | primary operational entry | One physical navigation entry only. |
| B | related record panel | No top-level duplicate. |
| C | detail action | No global navigation entry. |
| D | supporting object | Access through its owner or operational center. |
| E | global native module | Remains global and appears exactly once. |
| F | derived/analytics object | Dashboard-only; no operational tab. |

The C17 classifications are: `ProspectingDashboard` A, `ProspectingSearch` A,
`Lead` E, `ResearchEvidence` D, `DraftApproval` A, `SendExecution` B,
`ReplyEvent` B, `EmailEvent` D, `SalesFeedback` D, `LearningSignal` F,
`Quote` A, `Approval` B, `ProformaInvoice` B, and `QuoteItem` D.

`Lead` is a native global module and must never be duplicated under the
Prospecting divider. Scope `tab` flags remain capability declarations, not
navigation placement controls.

## Non-negotiable Boundaries

- No second `ConfigWriter`/`tabList` writer.
- No scope `tab` changes for navigation placement.
- No duplicated `Lead` entry.
- No change to existing relationship-panel access paths.
- No workflow, ACL, connector, provider, worker, or entity design work.

## WP1.4 Follow-up

The approved product-polish audit refines physical ordering, Chinese-first
labels, dashboard consolidation, and release governance without changing this
architecture. See [WP1.4 audit](PHASE3C17_WP1_4_NAVIGATION_PRODUCT_POLISH_AUDIT.md).
