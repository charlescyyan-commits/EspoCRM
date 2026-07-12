# Chitu Prospecting Integration — EspoCRM Extension Skeleton V1

**Phase:** 3B01  
**Version:** `1.1.0-alpha`  
**Status:** CRM entity model only; no new sync endpoint, email sending, or AI runtime

## Purpose

Installable EspoCRM extension skeleton for a future one-way Prospecting Engine → EspoCRM integration.

Frozen Phase 3A-1 principles:

1. Prospecting Engine is the business source of truth.
2. EspoCRM is the sales execution layer.
3. Data direction is Engine → EspoCRM only.
4. Future sync requires `qualification_status = OUTREACH_READY`.
5. V4-only: `score_rules_version` must identify Canonical Scoring V4.
6. Account and Opportunity are never auto-created.

## Package Layout

```text
espocrm_extension/
├── manifest.json                 # EspoCRM extension manifest
├── Resources/                    # Design-surface copies of metadata
│   ├── entityDefs/
│   ├── layouts/
│   ├── acl/
│   └── metadata/
├── files/                        # EspoCRM installable package root (required lowercase)
│   └── custom/Espo/Modules/Prospecting/
├── custom/Espo/Modules/Prospecting/   # Module placeholders (Controllers/Services/Api)
├── application/                  # Reserved placeholder (not packaged into EspoCRM)
├── scripts/                      # Future BeforeInstall/AfterInstall hooks
├── docs/
└── tests/
```

EspoCRM packages require a lowercase `files/` directory. On Windows this collides with a capital `Files/` name, so the skeleton uses `files/` plus a top-level `application/` placeholder.

## Entities

| Entity | Role in V1 skeleton |
|---|---|
| `ResearchEvidence` | Custom evidence entity linked 1:N to native Lead |
| `Lead` | Metadata overlay for Chitu source, classification, opportunity, research, and contact context |
| `Opportunity` | Metadata overlay for recommendation, product fit, cooperation type, and next action |

## Not Implemented

- Engine API / import endpoint
- Sync controller / service
- Authentication
- Webhooks
- Automatic Lead / Account / Opportunity creation
- Email or AI calls
- Database migrations against a live CRM

## Install / Rollback

See `docs/espocrm-extension/ESPOCRM_EXTENSION_INSTALL_GUIDE_V1.md`.

## Tests

```bash
python -m unittest espocrm_extension.tests.test_extension_skeleton -v
```

## Next Phase

Phase 3A-2.2 may implement Controllers / Services / Api under the Prospecting module after explicit authorization.
