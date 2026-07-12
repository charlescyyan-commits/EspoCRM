# Prospecting Module Placeholders

This directory reserves the EspoCRM module namespace:

`custom/Espo/Modules/Prospecting/`

## Installable Source of Truth

The installable module metadata and layouts live under:

`files/custom/Espo/Modules/Prospecting/`

EspoCRM copies everything under `files/` into the CRM root on extension install.

## Subdirectories

| Path | Phase 3A-2.1 | Phase 3A-2.2 intent |
|---|---|---|
| `Controllers/` | README only | Authenticated import controller |
| `Services/` | README only | Contract validation, idempotency, sync |
| `Api/` | README only | Narrow import route definitions |

Do not add PHP controllers, services, or API routes in this phase.
