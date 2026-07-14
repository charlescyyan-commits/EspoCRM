# API Documentation

API documentation for the EspoCRM Production workspace. All endpoints listed here exist in `crm-extension/Resources/routes.json` unless marked otherwise.

## Scope

| Surface | Document |
|---------|----------|
| CRM custom REST actions | [REST_ENDPOINTS.md](REST_ENDPOINTS.md) |
| Python connector client | [CONNECTOR_API.md](CONNECTOR_API.md) |
| Webhooks | [WEBHOOKS.md](WEBHOOKS.md) |
| Sync JSON contract | [../sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json](../sync-contracts/ESPOCRM_SYNC_CONTRACT_V1.json) |

## Authentication

**Status:** Implemented (pattern)

Custom Prospecting routes use EspoCRM API authentication:

- Header: `X-Api-Key: <api-key>` (standard EspoCRM API key)
- ACL enforced per entity scope in service classes (`Acl::check`, `checkEntityEdit`, etc.)

Do not document or commit real API keys. Integration Bot role is provisioned by deployment scripts for test environments.

## Implementation Status Summary

| Endpoint group | CRM adapter | Connector client |
|----------------|-------------|------------------|
| Sync (lead/evidence/proposal) | **Implemented** | **Implemented** |
| Feedback sync | **Implemented** | **Implemented** |
| Brevo email event | **Implemented** | **Implemented** |
| Search strategy generate-jobs | **Implemented** | **Not Implemented** (UI uses CRM session) |
| Acquisition job runner | Uses EspoCRM standard REST (`SearchJob`, `ProspectPool`) | **Implemented** (connector CLI; fake provider) |

## Status Labels

See [../README.md](../README.md#status-labels) for definitions of Implemented, Contract Defined, Draft, etc.

## Related Documents

- [REST_ENDPOINTS.md](REST_ENDPOINTS.md)
- [CONNECTOR_API.md](CONNECTOR_API.md)
- [../architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md)
