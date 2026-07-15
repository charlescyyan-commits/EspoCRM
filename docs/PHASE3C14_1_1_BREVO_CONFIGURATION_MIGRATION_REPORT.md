# Phase3C14.1.1 Brevo Runtime Configuration Migration Audit

## Result

BLOCKED

## Scope

This audit covers only the runtime configuration boundary for C14.1 live Brevo acceptance. It does not modify the ProviderAdapter, worker, C10-C13 contracts, CRM entities, projection, queue behavior, or provider behavior. No email was sent and no secret value was read, copied, or written.

## Runtime Environment Verification

The current EspoCRM-Production process environment was checked by presence only.

| Required variable | Current runtime result |
|---|---|
| `BREVO_API_KEY` | MISSING |
| `BREVO_SENDER_EMAIL` | MISSING |
| `BREVO_TEST_RECIPIENT` | MISSING |

The C14.1 live acceptance precondition is therefore not met.

## New Project Runtime Injection Mechanism

The verified configuration boundary in EspoCRM-Production is the process environment:

- `chitu-connector/chitu_connector/espocrm_sync/brevo_provider.py` reads `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, and optional `BREVO_SENDER_NAME` using `os.environ`.
- The adapter has no dotenv loader and no literal Brevo-key pattern.
- The repository contains no discovered Docker Compose, Railway, Nixpacks, or other deployment secret-injection manifest. The deployment platform/host must inject environment variables outside the repository.
- `.gitignore` excludes `.env`, `.env.*`, credentials, and secret files. No target-project `.env*` file is present or tracked.

`BREVO_TEST_RECIPIENT` is an acceptance-only runtime input. It is not provider-adapter configuration and must be injected only for the controlled C14.1 test process.

## Original Project Configuration Source

The migration source was inspected without reading values:

- `D:\Chitu-intelligence\app\backend\services\brevo_sender.py` uses `os.getenv` for `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, and `BREVO_SENDER_NAME`.
- A local `.env` file exists in the original project but was not read. Git tracks only `.env.example`, not the local `.env`.
- A separate legacy delivery utility matched a literal-key safety pattern. Its value was not read or copied. It must not be used as a migration source; the existing credential should be reviewed and rotated by the secret owner if that match is confirmed.

## Migration Plan

1. Obtain the current Brevo credential only through the approved secret owner or deployment secret manager; do not extract it from source files, Git history, documentation, logs, or local files.
2. Configure the EspoCRM-Production runtime host/service secret store to inject:
   - `BREVO_API_KEY`
   - `BREVO_SENDER_EMAIL`
   - `BREVO_TEST_RECIPIENT`
3. Restrict `BREVO_TEST_RECIPIENT` to a controlled internal mailbox and use a sender identity authorized by the Brevo account.
4. Restart or redeploy only the target process so the three environment variables are inherited at startup.
5. Re-run C14.1 presence validation. Only after all three values are present may the single controlled Queue -> Worker -> BrevoProviderAdapter acceptance request be considered.

No source-code, Git, documentation, log, or local `.env` mutation is part of this plan.

## Secret Safety Verification

- No secret value was printed by this audit.
- No target-repository file matched the Brevo API-key signature scan, excluding local environment and log/archive paths.
- No target-project environment file is present or tracked.
- No configuration file, source file, or Git change was created by this audit before this report.
- The report names configuration keys only; it contains no credential, token, sender value, or recipient value.

## Entry Decision

**BLOCKED**

External runtime secret injection is required before C14.1 can continue. Do not implement a workaround, place values in the repository, or start C14.2.

