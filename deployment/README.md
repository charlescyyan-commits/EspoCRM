# Deployment Assets

| Path | Role |
| --- | --- |
| `railway/` | **C25 staging** Railway Dockerfile scaffold (see `railway/README.md`) |
| `docker/` | Reserved operational boundary (empty unless a future approved stack is added) |
| `backup/` | Reserved operational boundary — no production credentials |
| `provisioning/` | Disposable CRM role/provisioning scripts — do not run without an approved target |
| `validation/` | Offline / API acceptance helpers |
| `prospecting-extension-*.zip` | Built extension packages + `.sha256` sidecars |

Staging Railway deploys must use `deployment/railway/Dockerfile` with repository-root build context. Production promotion is out of scope for the Railway staging scaffold.
