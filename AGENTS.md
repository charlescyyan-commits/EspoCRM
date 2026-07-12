# EspoCRM Production Workspace Instructions

## Allowed

- EspoCRM extension development
- Chitu-to-EspoCRM connector integration
- CRM deployment preparation
- CRM tests, backups, provisioning, and rollback documentation

## Forbidden

- Modify Chitu scoring logic
- Modify AI research logic
- Modify the email-generation engine
- Modify unrelated Chitu application code
- Import real customer data or enable outreach without explicit approval

Keep the connector independent by importing only `chitu_connector` and its vendored stable interfaces.
