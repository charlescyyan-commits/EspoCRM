# Webhooks

**Status:** **Not Implemented**

## Current State

This repository does **not** implement a generic EspoCRM webhook framework or outbound webhook dispatcher.

Searches of `crm-extension/` and `chitu-connector/` show no webhook registration, signature verification, or callback URL configuration for third-party systems.

## Related Inbound Endpoints (Not Webhooks)

The following are **custom REST POST actions**, not webhook infrastructure:

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /Prospecting/brevo/email-event` | Ingest Brevo-style email execution events | **Implemented** |
| `POST /Prospecting/feedback/sync` | Ingest sales feedback from connector | **Implemented** |
| `POST /Prospecting/sync/*` | Connector-driven sync | **Implemented** |

These require EspoCRM API authentication (`X-Api-Key`) and are called by trusted clients, not registered as EspoCRM outbound webhooks.

## Historical References

Early workflow design documents mention webhook-style email status flows. Those describe **design intent**, not current code. See [../workflow/PHASE3A25_WORKFLOW_DESIGN.md](../workflow/PHASE3A25_WORKFLOW_DESIGN.md) for historical context only.

## Future Work

Any future webhook support would require explicit ADR and phase authorization. Do not assume webhook URLs or payloads from design docs.
