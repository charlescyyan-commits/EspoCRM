# Release Notes: 1.9.10-alpha

**Artifact:** `deployment/prospecting-extension-1.9.10-alpha.zip`
**Integrity sidecar:** `deployment/prospecting-extension-1.9.10-alpha.zip.sha256`

## Phase3C17 Command Center composition (CC-0B / CC-1)

- Hardens Sales Development Command Center provisioning (`--user`,
  `--user=all`, `--dev-defaults`) without login hooks or ACL changes.
- Composes the Chinese-first primary dashboard tab `销售开发指挥中心` with
  operational summaries and five daily queues: 我的任务, 待研究客户, 待触达,
  待回复, 待审批.
- Updates ProspectingSummary dashlet presentation for center composition.
- Preserves personal dashboards (e.g. My Espo); does not change navigation,
  workflow ownership, Quote/Approval mutation paths, or ACL.

## Integrity

`1.9.10-alpha` is a new deterministic canonical artifact. The prior
`1.9.9-alpha` ZIP and SHA-256 sidecar remain immutable historical evidence.

## Scope disclosure

This alpha release packages Command Center presentation/composition only.
It adds no new scopes, no workflow mutation, no ACL changes, and no
navigation IA changes. New-user default dashboard assignment remains a
documented known risk (provisioner re-run or native Dashboard Templates).
