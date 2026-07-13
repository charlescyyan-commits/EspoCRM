# Phase3B Architecture Snapshot

```text
Chitu Intelligence
  search / research / scoring / AI analysis
                    |
                    v
Connector Contract V1
                    |
                    v
chitu_connector
  authentication / validation / mapping / idempotent transport
                    |
                    v
EspoCRM Prospecting Extension
  Lead projection
  ResearchEvidence append-only evidence
  Opportunity Proposal metadata projection
  SalesFeedback and LearningSignal persistence
  native filters, dashboards, and relationships
                    |
                    v
CRM Sales Operations
  human judgment / stages / follow-up / tasks / outcomes
                    |
                    v
Dashboard and Workflow
  role-compatible queues / review / sync diagnostics
```

## Ownership

| Layer | Responsibility |
|---|---|
| Chitu Intelligence | Search, research, scoring, and AI analysis |
| Connector | Stable V1 transport, authentication, mapping, and idempotency |
| EspoCRM extension | CRM-safe projection, evidence, feedback entities, filters, dashboards, and workflow metadata |
| CRM users | Sales decisions, follow-up, customer outcomes, and manual opportunity handling |

## Boundaries

- EspoCRM does not run DeepSeek, duplicate the scoring engine, or modify the prospecting engine.
- Research evidence is appended rather than silently overwritten.
- Proposal fields remain Lead metadata; no automatic Opportunity is created.
- Feedback synchronization is authenticated and idempotent.
- Role-specific dashboards respect existing ACLs without widening permissions.
- Email provider execution remains outside this CRM extension.

