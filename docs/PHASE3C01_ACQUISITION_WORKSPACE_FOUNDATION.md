# Phase3C01: AI Acquisition Workspace Foundation

## Scope

This phase creates the CRM-side acquisition workspace only. It does not implement search algorithms, research algorithms, scoring, AI runtime, a connector import endpoint, or automatic CRM Lead creation.

- Extension version: `1.8.0-alpha`
- Package: `deployment/prospecting-extension-1.8.0-alpha.zip`
- SHA-256: `249FEBD4C2E13851B79C1AB198DABA285324C7FD83202A553D557771237AE957`

## Workspace

The `Acquisition` dashboard tab contains:

- Discovery Jobs
- Running, Waiting, Completed, and Failed Search Job queues
- Lead Pool
- Research Queue

## Model

`SearchJob` is the management record for every future acquisition request. It stores keyword, country, strategy, status, source, creation time, completion time, result count, and failure reason.

`ProspectPool` is a raw prospect record, not a CRM Lead. Each item belongs to one Search Job and exactly one pipeline queue: `DISCOVERY`, `QUALIFICATION`, `RESEARCH`, or `CRM`.

The foundation records research, qualification, and CRM-push readiness only. A future approved connector flow may act on a `QUALIFIED` prospect in the CRM queue; this phase does not create, update, or link CRM Leads automatically.

## Provisioning

After installing the extension and running rebuild/clear-cache, provision the dashboard for an existing user:

```text
php /tmp/phase3c01_provision_acquisition_workspace.php admin
```

The script is idempotent for `phase3c01-*` dashboard entries and changes only the selected user's dashboard preferences.

## Boundary

Chitu Intelligence continues to own search, research, scoring, and AI analysis. EspoCRM owns work management and human review of the acquisition pipeline.

## Static Validation

- Extension metadata tests: `36 PASS`
- JSON syntax and duplicate-key validation: `103 PASS`
- Package manifest version: `1.8.0-alpha`
- No local runtime installation, synthetic data creation, CRM Lead creation, or search execution was performed in this phase.
