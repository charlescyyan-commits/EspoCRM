# Phase3C17 WP1.4 — Navigation Product Polish Audit

**Status:** Approved with refinements

## Product Decision

The product is Chinese-first. It must not add a top-level `情报中心` tab or a
top-level `业务中心` tab. `情报中心` remains a dashboard/card concept; research
records remain accessed through native `Lead` and its relationship panels.

## Final Navigation IA

`Home` is the native first entry. The governed `config.tabList` order is:

```text
潜客开发
  潜客运营          ProspectingDashboard
  搜索中心          ProspectingSearch
  触达中心          DraftApproval
  报价中心          Quote
客户管理
  Account / Contact / Lead / Opportunity
活动
  Email
更多
  Task / Calendar / KnowledgeBaseArticle
```

`ResearchEvidence`, `Approval`, `ProformaInvoice`, `QuoteItem`, `EmailEvent`,
and `LearningSignal` are not top-level entries. Unmanaged native tools remain
available after the governed product order; they are not disabled.

## Homepage Consolidation

Provision one primary dashboard named `销售开发指挥中心`. Preserve `My Espo` and
non-phase dashlets. Merge the historical `Prospecting Operations`,
`Acquisition`, and `Prospecting Home` phase-managed content into the command
center using only existing extension dashlets and EspoCRM's native `Records`
dashlet.

The intended bands are:

1. Operational summaries.
2. `我的任务`, `待研究客户`, `待触达`, `待回复`, and `待审批`.
3. `客户池`, `新增客户`, and research-completion activity.

No database metric, PHP service, endpoint, role, ACL, or entity is introduced.

## Localization Decisions

- `ProspectingDashboard` is `潜客运营` in `zh_CN`.
- Required Chinese scope names: `发送执行`, `客户回复`, `邮件事件`, `销售反馈`, and `学习信号`.
- Required singular names: `触达审批`, `报价`, and `报价审批`.
- Four operational-center dashboard cards and descriptions use `Global.labels`
  i18n keys with exact `en_US`/`zh_CN` key parity.

## Release Governance

The immutable `1.9.7-alpha` artifact is retained. A source/package change must
be promoted as a new `1.9.8-alpha` canonical artifact with a new SHA-256
sidecar and artifact check; it must never overwrite `1.9.7-alpha`.

## Deferred Items

No analytics redesign, new navigation framework, generic CRM feature removal,
or C16 workflow change is approved by this audit.
