# Phase3C14.3.1B-3 Payload Snapshot Implementation Report

## Result

**PASS WITH RISKS**

The connector now has a durable, immutable payload-snapshot boundary.  It
persists approved delivery content in a connector-owned SQLite database and
can reopen and verify the same snapshot from a new store instance.  The
implementation has no CRM, Worker, Queue, Provider, Brevo, retry, or network
dependency.

The remaining risk is deployment-owned: raw payload content requires an
encrypted connector persistent volume (or an encrypted connector-owned
database) and access restricted to the connector service identity.  B-3 does
not make the current C13 in-memory Queue durable and does not implement
end-to-end crash recovery.

## Files Changed

| File | Change |
|---|---|
| `chitu-connector/chitu_connector/espocrm_sync/payload_snapshot.py` | Added immutable model, deterministic SHA-256 hashing, secret ingress guard, SQLite persistence protocol/adapter, and self-verifying reads. |
| `tests/test_phase3c14_3_1b3_payload_snapshot.py` | Added deterministic, immutability, validation, secret-scan, restart-persistence, and dependency-isolation tests. |
| `docs/PHASE3C14_3_1B3_PAYLOAD_IMPLEMENTATION_REPORT.md` | Added this implementation record. |

## Snapshot Design

`PayloadSnapshotInput` is accepted only at an authorized connector payload
ingress.  It requires:

- `execution_id`;
- approved `content_hash` (lowercase SHA-256 reference);
- recipient, subject, body, and campaign reference; and
- timezone-aware `payload_created_at`.

`PayloadSnapshot` is a frozen dataclass and contains at least the required
fields:

| Field | Behavior |
|---|---|
| `snapshot_id` | Deterministic `payload:<snapshot_hash>` identifier. |
| `execution_id` | Unique persisted execution identity. |
| `content_hash` | Existing approved-content reference; syntax-validated, retained without CRM access. |
| `recipient_hash` | SHA-256 of normalized recipient, compatible with the B-1 safe reference. |
| `payload_created_at` | Source timestamp; timezone-aware and persisted. |
| `schema_version` | `phase3c14.3.1b3-payload-snapshot-v1`. |
| `snapshot_hash` | Deterministic SHA-256 of canonical execution/content fields. |
| recipient, subject, body, campaign reference | Raw delivery payload, hidden from normal dataclass `repr`. |

The snapshot hash is calculated from canonical JSON containing execution id,
approved content hash, recipient hash, subject, body, campaign reference, and
schema version.  Timestamps are deliberately excluded so the same execution
and content generate the same snapshot hash.  A read recomputes recipient and
snapshot hashes; a mismatch fails with a safe integrity code rather than
returning unverifiable content.

`SqlitePayloadSnapshotStore.save_if_absent` is the only write operation.  Its
SQLite `BEGIN IMMEDIATE` transaction and primary key on `execution_id` make
the exact replay idempotent.  Any attempt to save different content under an
existing execution raises `PAYLOAD_IMMUTABILITY_CONFLICT`.  There is no update
or delete API in this phase.

## Storage Boundary

The storage adapter is connector-only and imports only Python standard-library
modules.  It uses a connector-owned SQLite file with transactional durability
settings (`WAL`, `synchronous=FULL`), parameterized SQL, and a new connection
per operation.  The reopen test proves data is recovered by a new store
instance rather than process memory.

The adapter deliberately is **not yet wired** to the B-2
`ApprovedDeliveryPayloadSource` or C13 `SendExecutionWorkStore`.  This phase
implements the approved persistence primitive only; it does not alter the
bridge, Worker, or Queue.  A future explicitly approved composition phase can
consume this store without giving the Worker CRM access.

## Security Review

Raw recipient, subject, and body are needed to preserve an execution payload,
so they are stored only inside the connector SQLite snapshot record.  The
following controls are present:

- raw payload fields are excluded from dataclass `repr`;
- the store has no logging, HTTP, CRM, Provider, Queue, or Worker dependency;
- parameterized SQL is used for every persisted value;
- ingress rejects credential-shaped patterns including API-key,
  authorization-header, bearer-token, password, secret, and token assignment
  patterns before persistence;
- raw content is not copied to bridge requests, CRM records, queue items, or
  result objects by this module; and
- the module stores no API key, authorization header, encryption key, or other
  secret field.

SQLite does not provide the key-management control itself.  Production must
put its database on a connector-owned encrypted persistent volume or use an
encrypted connector-owned database, with filesystem/database permissions
limited to the connector service identity.  That deployment prerequisite is
the reason for the `WITH RISKS` verdict.  Retention/deletion policy is deferred
until an explicitly approved operational phase; B-3 intentionally exposes no
mutable or deletion interface.

## Test Results

| Command | Result |
|---|---|
| `python -m py_compile chitu-connector/chitu_connector/espocrm_sync/payload_snapshot.py tests/test_phase3c14_3_1b3_payload_snapshot.py` | PASS |
| `python -m unittest tests.test_phase3c14_3_1b1_bridge_contract tests.test_phase3c14_3_1b2_crm_bridge_adapter tests.test_phase3c14_3_1b3_payload_snapshot` | PASS — 21 tests |
| `python -m unittest discover -s chitu-connector/tests -p test_*.py` | PASS — 270 tests |

B-3 tests prove:

1. identical input produces the same snapshot hash, id, recipient hash, and
   idempotent persisted result;
2. changed body content produces a different snapshot hash;
3. dataclass fields cannot be mutated and an existing execution cannot be
   persisted with changed content;
4. all required fields and timestamps are validated and rejected when missing
   or malformed;
5. credential-shaped content is rejected before any SQLite row is created;
6. reopening the database through a new store instance returns the same
   self-verifying payload; and
7. source imports exclude CRM bridge adapter, Worker, Queue, Provider, Brevo,
   HTTP, and transport modules.

All tests use synthetic data and SQLite temporary files.  No external request
or send occurred.

## Compatibility

| Area | Result | Evidence |
|---|---|---|
| C10 | PASS | No C10 source, lifecycle, request identity, or idempotency contract changed. Snapshot idempotency is confined to `execution_id` and does not authorize a retry. |
| C11 | PASS | No CRM entity, metadata, schema, Lead projection, EmailEvent writer, or CRM runtime path changed. |
| C12 | PASS | No ProviderAdapter contract or implementation changed; payload module has no provider import. |
| C13 | PASS WITH RISKS | No Worker or Queue source changed or imported. Snapshot persistence can survive restart, while C13 Queue/claim durability remains explicitly deferred. |
| C14.2B | PASS | No failure classification, terminal network interpretation, retry behavior, Brevo code, or send behavior changed. |

## Scope Confirmation

| Question | Result |
|---|---|
| Was CRM modified? | No. |
| Was a CRM entity or schema created? | No. |
| Was the Worker modified? | No. |
| Was the Queue implementation touched? | No. |
| Was Provider/Brevo/retry/error classification modified? | No. |
| Was a real email sent? | No. |

## Next Recommended Phase

Subject to a separate approval, add an explicit connector composition layer
that adapts this durable store to B-2's `ApprovedDeliveryPayloadSource` while
preserving B-2 validation and keeping the Worker CRM-free.  Do not wire a
queue, Worker, result callback, retry policy, or production provider send
until each boundary has its own approved phase.
