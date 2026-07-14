# ACL (User Guide)

**Status:** Static Verified from provisioning scripts and metadata

## Acquisition Scopes

Provisioned by `deployment/provisioning/phase3c02_1_provision_acquisition_acl.php`:

| Role | SearchStrategy | SearchJob | ProspectPool |
|------|----------------|-----------|--------------|
| Admin | create/read/edit/delete all | same | same |
| Sales Manager | create/read/edit all; no delete | same | same |
| Sales User | create/read/edit own | same | same |
| Integration Bot | create/read/edit all; no delete | same | same |

## Prospecting / Lead Scopes

Workspace roles provisioned by `phase3b06_provision_workspace_roles.php`:

- ResearchEvidence: read-oriented for sales roles; restricted create
- Sensitive sync fields may be hidden per role (`peLastSyncAt`, etc.)
- Operations dashboards: `phase3b07_provision_operations_dashboards.php`

## Integration Bot

Used by connector for API sync. Requires API key with access to:

- `POST /Prospecting/sync/*`
- `POST /Prospecting/feedback/sync`
- `POST /Prospecting/brevo/email-event`
- Standard REST for runner (`SearchJob`, `ProspectPool`)

## UI Visibility

Dashlets and tabs respect `aclScope` in dashlet metadata. Users without scope access will not see Acquisition entities.

## Validation

Offline: `test_phase3c02_1_acquisition_acl_provisioning` in `test_extension_skeleton.py`

Live: `deployment/validation/phase3c02_1_api_acl_acceptance.py` — **TBD — requires runtime verification**

## Related Documents

- [INSTALL_EXTENSION.md](INSTALL_EXTENSION.md)
- [../PHASE3C02_1_ACQUISITION_ACL_REPORT.md](../PHASE3C02_1_ACQUISITION_ACL_REPORT.md)
