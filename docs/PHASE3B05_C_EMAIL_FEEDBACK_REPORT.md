# Phase3B05-C — Email Feedback Integration Report

**Date:** 2026-07-12  
**Workspace:** `D:\EspoCRM-Production`  
**Extension:** Chitu Prospecting Integration `1.5.2-alpha`  
**Runtime:** local EspoCRM-Test Docker stack  
**Status:** **PASS**  

**Pipeline:** Brevo → EmailEvent → EspoCRM Workflow → SalesFeedback → LearningSignal → Connector export → Chitu (consumer)

**Boundary:** Reuses Phase3B04 SalesFeedback/LearningSignal. Sync Contract V1 unchanged. No AI training. No second feedback system. EmailEvent contract fields unchanged.

---

## 1. Mapping

| EmailEvent.eventType | SalesFeedback.feedbackType | outcome | Notes |
|---|---|---|---|
| `REPLIED` | `CUSTOMER_REPLY` | `NEUTRAL` | Explicit reply mapping |
| `CLICKED` | `EMAIL_INTERESTED` | `POSITIVE` | Interest proxy from engagement |
| `BOUNCED` | `EMAIL_BOUNCED` | `NEGATIVE` | Delivery failure signal |
| `SENT` / `DELIVERED` / `OPENED` | — | — | No SalesFeedback (workflow-only) |

Additional feedback types (for Chitu-classified / FeedbackSync API, not EmailEvent-driven):

| feedbackType | Typical outcome | Use |
|---|---|---|
| `EMAIL_NOT_INTERESTED` | `NEGATIVE` | Connector/classified rejection |
| `EMAIL_NO_RESPONSE` | `NEUTRAL` | Connector/classified long no-reply |

Additive enum extension only; existing B04 types remain valid. Source value `EMAIL_EVENT` marks EmailEvent-derived feedback.

---

## 2. Feedback Rules

Implemented in `EmailEventSalesFeedbackHook` (after-save, order 30; after B05-B workflow hook):

1. On **new** EmailEvent with a mapped type, create one `SalesFeedback`.
2. Idempotency key: `externalFeedbackId = email-event:{EmailEvent.id}`.
3. Copies `campaign` from EmailEvent; `product` from Lead `peBestFirstProduct`.
4. Does **not** create LearningSignal directly — Phase3B04 `SalesFeedbackLearningSignalHook` remains the sole signal generator.

---

## 3. Learning Signal

Existing B04 hook updated only to copy optional `campaign` onto LearningSignal.

| Field | Source |
|---|---|
| `leadId` | SalesFeedback / Lead |
| `salesFeedbackId` | feedback id |
| `signalType` | feedbackType |
| `predictionScore` | Lead `peOpportunityScoreV4` |
| `actualOutcome` | feedback outcome |
| `product` | feedback product |
| `campaign` | feedback campaign (new optional field) |

---

## 4. Connector Export

Package: `chitu_connector.espocrm_sync.feedback_signal_export`

| Type | Role |
|---|---|
| `FeedbackSignalPayload` | `{lead_id, feedback_type, outcome, product, campaign, timestamp}` (+ optional ids) |
| `FeedbackSignalExportClient` | Authenticated `GET /api/v1/LearningSignal` with `X-Api-Key`; maps CRM rows to export payload for Chitu |

Does not push into Chitu runtime or train models — export-only typed client.

Inbound FeedbackSync API also accepts the new EMAIL_* types and optional `campaign` (additive; Sync Contract V1 untouched).

---

## 5. Security

| Check | Result |
|---|---|
| Brevo email-event without auth | HTTP **401** |
| LearningSignal list without auth | HTTP **401** |
| Integration Bot | create/read EmailEvent + SalesFeedback; read LearningSignal |
| Anonymous feedback injection | Blocked |

---

## 6. Validation

| Check | Result | Evidence |
|---|---|---|
| Extension build | PASS | `prospecting-extension-1.5.2-alpha.zip`; SHA-256 `BAFA7AD2617988308ED33288DF6744E6BEB548405AB11213CFE6D7005A834619` |
| Install / rebuild / cache clear | PASS | Installed `1.5.2-alpha` |
| Extension regression | PASS | `32` tests OK |
| Connector regression | PASS | `47` tests OK |
| REPLIED → SalesFeedback | PASS | `CUSTOMER_REPLY` / `NEUTRAL` / `email-event:{id}` |
| Interested (CLICKED) → Positive signal | PASS | `EMAIL_INTERESTED` / `POSITIVE` LearningSignal |
| Bounce → Negative signal | PASS | `EMAIL_BOUNCED` / `NEGATIVE` |
| Duplicate EmailEvent | PASS | duplicate=true; feedback count stayed 3 (no extra row) |
| Unauthorized | PASS | event + export **401** |
| Lead panels | PASS | emailEvents / salesFeedbacks / learningSignals metadata present |
| Cleanup | PASS | Synthetic records + API user removed |

---

## 7. Limitations

1. `EMAIL_NOT_INTERESTED` / `EMAIL_NO_RESPONSE` are not auto-derived from EmailEvent types (EmailEvent contract frozen); use FeedbackSync classification or future approved event enrichment.
2. `CLICKED` is the EmailEvent proxy for “interested”; human/Chitu may still post finer classifications via FeedbackSync.
3. Export is pull-oriented via authenticated LearningSignal API; Chitu ingestion/training is out of scope.
4. Browser UI click-through deferred (localhost policy); ORM + relationship panels verified.
5. Local EspoCRM-Test only.

---

## 8. Files

- `Hooks/EmailEvent/EmailEventSalesFeedbackHook.php` (new)
- SalesFeedback / LearningSignal entityDefs + i18n + layouts (`campaign`, EMAIL_* types, `EMAIL_EVENT` source)
- `SalesFeedbackLearningSignalHook.php` (campaign copy)
- `FeedbackSyncService.php` / `feedback_api.py` (additive EMAIL_* + campaign)
- `feedback_signal_export.py` + tests
- Lead relationship panels for salesFeedbacks / learningSignals
- `manifest.json` → `1.5.2-alpha`
- provisioning `phase3b05c_*.php`

---

**Phase3B05-C complete. Status: PASS.**

Do **not** enter Phase3B06 without explicit authorization.
