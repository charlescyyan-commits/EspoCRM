# Install Extension (User Guide)

**Status:** Static Verified (procedure); **Runtime Verified** on disposable instances per phase reports

## Audience

EspoCRM administrators installing **Chitu Prospecting Integration** on a test or approved production instance.

## Before You Install

- Confirm EspoCRM version `>=7.4.0`
- Confirm PHP `>=8.1` on server
- Use a **backup** on any non-disposable instance
- Obtain extension ZIP matching target version (currently `1.9.5-alpha`)

## Steps

1. Open **Administration → Extensions**.
2. Upload `prospecting-extension-<version>.zip` from `deployment/` (or freshly built package).
3. Click **Install** and wait for completion.
4. Run **Rebuild** if Administration prompts for cache/metadata rebuild.
5. Verify new tabs/scopes appear:
   - Leads show Prospecting intelligence sections
   - **Search Strategies**, **Discovery Jobs** (SearchJob), **Prospect Pool** (if ACL permits)

## After Install

| Task | Who | Notes |
|------|-----|-------|
| Role assignment | Admin | Run provisioning scripts or assign roles manually |
| Integration Bot API key | Admin | For connector sync — store securely |
| Dashboard setup | Admin | Acquisition dashboards via `phase3c01_provision_acquisition_workspace.php` |

## Uninstall

See [../deployment/ROLLBACK.md](../deployment/ROLLBACK.md).

## Related Documents

- [ACL.md](ACL.md)
- [../deployment/INSTALL.md](../deployment/INSTALL.md)
