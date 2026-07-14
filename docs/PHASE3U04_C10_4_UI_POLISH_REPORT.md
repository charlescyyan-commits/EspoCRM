# Phase3U04 - Prospecting UI Polish (C10.4 Compatible)

**Date:** 2026-07-14
**Status:** PASS
**Scope:** Native EspoCRM UI metadata only

## Result

Phase3U04 made one narrow presentation correction:

```text
ResearchEvidence: "AI Research Evidence" -> "Research Evidence"
```

The old navigation label incorrectly implied that the CRM entity contains AI-generated conclusions. The entity is the factual evidence store used by the Prospecting workflow; the current architecture keeps AI/research execution outside CRM. The corrected label is neutral, accurate, and follows EspoCRM's native entity naming pattern.

No other new UI metadata change was needed. The existing native U04 dashboard cleanup already provides compact `expandedLayout` rows for the Prospecting Operations record-list dashlets, and the current SearchStrategy, SearchJob, ProspectPool, and Lead Intelligence layouts already meet the requested business-first placement.

## Dashboard Review

`Prospecting Operations` remains a native EspoCRM dashboard surface:

- record-list dashlets use `views/dashlets/abstract/record-list`;
- dashlets declare compact, entity-specific `expandedLayout` rows;
- titles are business labels such as Search Strategies, Search Jobs, Queued Jobs, Running Jobs, Completed Jobs, Failed Jobs, Prospect Pool, and Research Queue;
- summary/recent-discovery dashlets retain their existing zero-safe empty handling;
- no SPA, React page, custom dashboard shell, fake metric, or dashboard placement PHP was introduced.

## Entity UI Review

| Surface | Finding | U04 action |
|---|---|---|
| SearchStrategy | Native strategy-definition, query-plan, and ownership sections; labels and empty-state wording are present. | No change. |
| SearchJob | Native layouts prioritize job status, strategy, provider, result count, and failure reason; internal fingerprint data is not promoted to the sales-facing layout. | No change. |
| ProspectPool | Native list/detail layouts lead with company, website, country, provider, and research status. | No change. |
| Lead Intelligence | Existing Lead layouts, Opportunity Proposal display fields, sales fields, and relationship panels remain intact. | No change. |
| ResearchEvidence navigation | Existing label was misleadingly AI-branded despite a factual evidence-only CRM boundary. | Corrected in `i18n/en_US/Global.json`. |

## C10.4 Protection

The U04 correction changes only the `ResearchEvidence` scope name and plural scope name. It does not declare, translate, reorder, or style approval, execution, reply, or email-lifecycle fields or their protected state values:

```text
READY_TO_SEND
APPROVED
SENT
FAILED
REPLIED
BOUNCED
```

The existing `Failed Jobs` dashlet title refers to the SearchJob dashboard and was not changed by U04; it is not a C10 send-execution state label. No layout, clientDef, dashlet, or language mapping for C10.1 approval, C10.2 provider adaptation, C10.3 controlled execution, or C10.4 reply tracking was changed. No lifecycle, approval, send, score, workflow, ACL, connector, PHP, or Python source was modified.

## Validation

| Check | Result |
|---|---|
| Extension static suite | PASS -- 57/57 |
| Metadata/package baseline | PASS -- 3/3 (all extension JSON parses; temporary package archive/install preflight passes) |
| Full connector suite | PASS -- 259/259, including the C10.4 reply-tracking boundary tests |
| C01--C10.4 source boundary | PASS -- UI-language-only change; no source files in those implementation layers changed |

Commands used:

```powershell
& <bundled-python> -m unittest discover -s crm-extension\tests -p 'test_*.py' -v

& <bundled-python> -m unittest discover -s tests\regression -p 'test_*.py' -v

$env:PYTHONPATH = 'D:\EspoCRM-Production\chitu-connector'
& <bundled-python> -m unittest discover -s chitu-connector\tests -p 'test_*.py' -v
```

## Files Changed by This Task

- `crm-extension/files/custom/Espo/Modules/Prospecting/Resources/i18n/en_US/Global.json`
- `docs/PHASE3U04_C10_4_UI_POLISH_REPORT.md`

No browser/runtime validation was run because the task is metadata-only and browser acceptance would require installing the extension and rebuilding EspoCRM metadata/cache in the shared runtime.
