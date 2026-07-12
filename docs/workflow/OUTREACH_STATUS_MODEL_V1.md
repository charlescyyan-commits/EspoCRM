# Outreach Status Model V1 — Chitu Intelligence → EspoCRM

> **Type:** Design Document (no implementation)
> **Date:** 2026-07-11
> **Status:** Draft for Review
> **Dependencies:** `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md`, `ESPOCRM_EXTENSION_ARCHITECTURE_PLAN_V1.md`

---

## Table of Contents

1. [Current System Field Analysis](#1-current-system-field-analysis)
2. [Outreach State Flow](#2-outreach-state-flow)
3. [CRM Entity Field Design](#3-crm-entity-field-design)
4. [Field-to-Entity Ownership Analysis](#4-field-to-entity-ownership-analysis)
5. [Implementation Recommendations](#5-implementation-recommendations)
6. [Gap Summary](#6-gap-summary)

---

## 1. Current System Field Analysis

### 1.1 Three Independent State Systems

The codebase currently runs **three separate state tracking systems** that do not share a unified schema:

| # | System | Location | Scope | Key States |
|---|--------|----------|-------|------------|
| 1 | **Engine State Machine** | `prospecting_engine/domain/state_machine.py` | Pre-CRM pipeline | `DISCOVERED` → `PRE_SCREENED` → `RESEARCHING` → `SCORED` → `ENRICHED` → `OUTREACH_READY` → `SYNCED_TO_ESPO` |
| 2 | **DB Pipeline Stage** | `app/backend/services/pipeline_stage.py` | Internal lead workflow | `new` → `enriching` → `scored` → `qualified` → `drafted` → `approved` → `queued` → `sent` → `responded` |
| 3 | **Event Bus** | `app/backend/core/event_bus.py` + `event_handlers.py` | CRM event-driven chain | `LeadCreated` → `LeadScored` → `LeadQualified/LeadRejected` → `OutreachTriggered` → `EmailSent` → `ReplyReceived` |

**These three systems overlap but are not unified.** For example, `OUTREACH_READY` in System 1 roughly corresponds to `qualified` in System 2 and `LeadQualified` in System 3, but the transition rules differ.

### 1.2 Current Database Tables — Outreach-Related

#### `leads` Table (PostgreSQL `schema.sql`)

| Column | Type | Current Values / Usage |
|--------|------|----------------------|
| `lead_status` | TEXT | `DISCOVERED`, `CREATED`, `DECIDED`, `QUALIFIED`, `DRAFTED`, `REJECTED`, `SENT`, `REPLIED_POSITIVE` — set by event_handlers |
| `pipeline_stage` | TEXT | `new`, `enriching`, `enriched`, `scoring`, `scored`, `qualified`, `drafting`, `drafted`, `approved`, `queued`, `sent`, `responded`, `rejected` — controlled by `pipeline_stage.py` |
| `outreach_status` | TEXT | `none`, `pending`, `queued`, `sent`, `responded`, `opted_out`, `BLOCKED`, `UNSUBSCRIBED` — set by `auto_outreach.py` and `brevo_webhook_handler.py` |
| `engagement_status` | TEXT | `cold`, `delivered`, `warming`, `warm`, `hot`, `inactive`, `removed` — computed by `brevo_webhook_handler.py` |
| `engagement_score` | REAL | Cumulative webhook signal weight |
| `total_opens` | INTEGER | Aggregated from webhook events |
| `total_clicks` | INTEGER | Aggregated from webhook events |
| `last_engagement_at` | TIMESTAMPTZ | Last open/click timestamp |
| `last_event_type` | TEXT | Last webhook event type string |

#### `email_drafts` Table

| Column | Type | Current Values |
|--------|------|---------------|
| `status` | TEXT | `Drafted` (default) |
| `approval_status` | TEXT | No enforced enum |
| `sent_at` | TIMESTAMPTZ | Set on send |
| `replied_at` | TIMESTAMPTZ | Set on reply |
| `opens_count` | INTEGER | Incremented by webhook handler |
| `clicks_count` | INTEGER | Incremented by webhook handler |
| `first_opened_at` | TIMESTAMPTZ | Set on first open event |
| `last_event_at` | TIMESTAMPTZ | Updated on each webhook event |
| `performance_score` | REAL | -1.0 for bounced; positive for engagement |

#### `email_outreach` Table (3-email sequence)

| Column | Type | Current Values |
|--------|------|---------------|
| `email_index` | INTEGER | 1–3 (UNIQUE per lead) |
| `status` | TEXT | `draft`, `approved`, `queued`, `sent` |
| `follow_up_date` | DATE | Scheduled follow-up |
| `sent_at` | TIMESTAMPTZ | Set on send |
| `approved_at` | TIMESTAMPTZ | Set on approval |

#### `email_log` Table (outbound audit)

| Column | Type | Current Values |
|--------|------|---------------|
| `status` | TEXT | `pending`, `sent`, `failed`, `bounced` |
| `sent_at` | TIMESTAMPTZ | Default now() |
| `provider` | TEXT | `brevo`, `smtp` |

#### `outreach_queue` Table (auto_outreach)

| Column | Type | Current Values |
|--------|------|---------------|
| `status` | TEXT | `pending_review`, `approved`, `queued`, `sent` |
| `approved_at` | TIMESTAMPTZ | Set on approval |
| `scheduled_at` | TIMESTAMPTZ | Set on scheduling |

#### `outreach_events` Table

| Column | Type | Current Values |
|--------|------|---------------|
| `event_type` | TEXT | Provider event type |
| `reply_status` | TEXT | Reply classification |
| `bounce_status` | TEXT | Bounce classification |
| `sent_at` | TIMESTAMPTZ | Send timestamp |

#### `email_reply_log` Table

| Column | Type | Current Values |
|--------|------|---------------|
| `reply_type` | TEXT | `positive`, `neutral`, `negative`, `no_reply` |
| `reply_timestamp` | TIMESTAMPTZ | When reply received |
| `source` | TEXT | `manual`, `simulated`, `webhook`, `inbox_scan` |

#### `follow_up_queue` Table

| Column | Type | Current Values |
|--------|------|---------------|
| `status` | TEXT | `pending`, `generated`, `sent`, `dismissed` |
| `follow_up_required` | BOOLEAN | Flag for re-engagement |
| `days_since_send` | INTEGER | Days since last email |
| `priority` | INTEGER | 0–10 |

#### `campaign_sequences` Table (V4 campaign strategy)

| Column | Type | Current Values |
|--------|------|---------------|
| `status` | TEXT | `draft`, `active`, `paused`, `completed`, `cancelled` |
| `value_tier` | TEXT | `high`, `medium`, `low` |
| `total_steps` | INTEGER | 2, 3, or 4 |
| `current_step` | INTEGER | 0–total_steps |
| `steps_config` | JSONB | Serialized CampaignStep array |

#### `email_events` Table (Brevo webhook raw events)

| Column | Type | Current Values |
|--------|------|---------------|
| `event_type` | TEXT | `delivered`, `opens`, `clicks`, `bounce`, `hard_bounce`, `soft_bounce`, `blocked`, `spam`, `unsubscribed`, `complaint`, `error`, `deferred`, `unique_opened` |
| `classification` | TEXT | `DELIVERY_SUCCESS`, `ENGAGED`, `HIGH_INTENT`, `INVALID_EMAIL`, etc. |
| `score_signal` | JSONB | `{signal, weight, reason}` |

#### `lead_event_log` Table (Immutable CRM event timeline)

| Column | Type | Valid Event Types |
|--------|------|------------------|
| `event_type` | TEXT | `LeadCreated`, `LeadScored`, `LeadEnriched`, `LeadQualified`, `LeadRejected`, `OutreachTriggered`, `EmailSent`, `ReplyReceived`, `PipelineStarted`, `PipelineCompleted` |

### 1.3 Brevo Webhook Event Classification

From `brevo_webhook_handler.py`, the event → classification mapping:

| Brevo Event | Classification | Signal | Weight |
|------------|----------------|--------|--------|
| `delivered` | `DELIVERY_SUCCESS` | neutral | 0.0 |
| `opens` | `ENGAGED` | positive | +1.0 |
| `unique_opened` | `FIRST_ENGAGEMENT` | positive | +1.5 |
| `clicks` | `HIGH_INTENT` | positive | +2.0 |
| `bounce` / `hard_bounce` | `INVALID_EMAIL` | negative | -1.0 |
| `soft_bounce` | `SOFT_BOUNCE` | neutral | -0.5 |
| `blocked` | `BLOCKED_BY_PROVIDER` | negative | -0.5 |
| `spam` / `complaint` | `BLACKLIST_TRIGGER` | negative | -2.0 |
| `unsubscribed` | `REMOVE_FROM_POOL` | negative | -2.0 |
| `error` | `DELIVERY_ERROR` | neutral | 0.0 |
| `deferred` | `DELIVERY_DEFERRED` | neutral | 0.0 |

### 1.4 Engagement Status Machine (Brevo)

From `brevo_webhook_handler.py` `compute_engagement_status()`:

```
                         ┌──────────────┐
                         │     cold     │  (initial)
                         └──────┬───────┘
                                │ delivered event
                         ┌──────▼───────┐
                         │  delivered   │
                         └──────┬───────┘
                                │ first open (opens > 0)
                         ┌──────▼───────┐
                         │   warming    │
                         └──────┬───────┘
                                │ opens > 2 OR clicks > 0
                         ┌──────▼───────┐
                         │    warm      │
                         └──────────────┘

Negative branches:
  spam / complaint / unsubscribed → removed
  bounce / hard_bounce / soft_bounce / blocked → inactive
```

### 1.5 Existing EspoCRM Lead Fields (Prospecting Extension)

From `espocrm_extension/Resources/entityDefs/Lead.json`:

| Field | Type | Current Role |
|-------|------|-------------|
| `peQualificationStatus` | varchar(64) | **The only outreach-related field** — stores a single text value |
| `peOpportunityScoreV4` | float | Score 0–100 |
| `peScoreTier` | enum (A/B/C) | Score tier |
| `peConfidence` | float | 0–1 |
| `peEvidenceCoverage` | float | 0–1 |
| `peBestFirstProduct` | varchar(255) | Recommended product |
| `peEngineVersion` | varchar(64) | Engine provenance |
| `peScoreRulesVersion` | varchar(64) | Scoring rules provenance |

**Critical Gap:** `peQualificationStatus` is the sole outreach status field. It cannot express:
- Email lifecycle (draft → approved → sent → delivered → opened → clicked → replied)
- Multi-email sequences (3-email rotation per CLAUDE.md rules)
- Campaign membership
- Follow-up scheduling
- Engagement scoring
- Reply classification

---

## 2. Outreach State Flow

### 2.1 Full Lifecycle State Machine

The following is the **unified** outreach lifecycle — spanning Engine → EspoCRM → Email Provider → Reply. It merges and standardizes the three independent state systems identified above.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTREACH LIFECYCLE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 0: DISCOVERY (Engine-only, pre-CRM)
─────────────────────────────────────────
    DISCOVERED ──→ PRE_SCREENED ──→ RESEARCHING ──→ RESEARCHED ──→ SCORED ──→ ENRICHED
                                                                                  │
PHASE 1: QUALIFICATION (Sync boundary)                                           │
─────────────────────────────────────────                                         │
    OUTREACH_READY ──→ APPROVED_FOR_CRM ──→ SYNCED_TO_ESPO                       │
                                                                                  │
    [At this point, the Lead exists in EspoCRM with outreachStatus = DISCOVERED]  │
                                                                                  │
PHASE 2: OUTREACH PREPARATION (EspoCRM)                                          │
─────────────────────────────────────────                                         │
    DISCOVERED ──→ RESEARCHING ──→ RESEARCH_COMPLETED ──→ QUALIFIED               │
                                                                     │            │
PHASE 3: DRAFT & APPROVAL (EspoCRM)                                 │            │
─────────────────────────────────────────                            │            │
    QUALIFIED ──→ OUTREACH_READY ──→ DRAFT_CREATED ──→ WAITING_APPROVAL           │
                                                                     │            │
PHASE 4: SENDING (EspoCRM → Email Provider)                          │            │
─────────────────────────────────────────                             │            │
    WAITING_APPROVAL ──→ APPROVED ──→ QUEUED ──→ SENT                             │
                                                     │                           │
PHASE 5: DELIVERY TRACKING (Email Provider → EspoCRM via Webhook)   │           │
─────────────────────────────────────────                             │           │
    SENT ──→ DELIVERED ──→ OPENED ──→ CLICKED                                    │
     │          │                                                               │
     │          └──→ BOUNCED (terminal)                                         │
     │          └──→ BLOCKED (terminal)                                         │
     └─────────────→ FAILED (retryable)                                         │
                                                                                │
PHASE 6: REPLY & CONVERSION (EspoCRM)                                           │
─────────────────────────────────────────                                        │
    OPENED/CLICKED ──→ REPLIED ──→ MEETING_BOOKED ──→ WON                       │
                          │                    │                                 │
                          ├──→ NEGATIVE_REPLY   ├──→ LOST (terminal)            │
                          ├──→ NEUTRAL_REPLY    └──→ NURTURING (re-engage)      │
                          └──→ NO_REPLY (auto follow-up)                        │
                                                                                │
PHASE 7: TERMINAL STATES                                                        │
─────────────────────────────────────────                                        │
    WON        — Deal closed, products shipped/ordered                          │
    LOST       — Explicit decline or competitor win                             │
    UNSUBSCRIBED — Recipient opted out                                          │
    BOUNCED    — Invalid email, hard bounce                                     │
    BLOCKED    — Marked as spam or provider-blocked                             │
    DISQUALIFIED — Manual review rejected the lead                              │
```

### 2.2 Transition Rules (Formal)

```
DISCOVERED          → { RESEARCHING, DISQUALIFIED }
RESEARCHING         → { RESEARCH_COMPLETED, DISQUALIFIED }
RESEARCH_COMPLETED  → { QUALIFIED, DISQUALIFIED }
QUALIFIED           → { OUTREACH_READY, DISQUALIFIED }
OUTREACH_READY      → { DRAFT_CREATED, DISQUALIFIED }
DRAFT_CREATED       → { WAITING_APPROVAL, OUTREACH_READY }
WAITING_APPROVAL    → { APPROVED, DRAFT_CREATED, DISQUALIFIED }
APPROVED            → { QUEUED, WAITING_APPROVAL }
QUEUED              → { SENT, FAILED, CANCELLED }
SENT                → { DELIVERED, BOUNCED, BLOCKED, FAILED }
DELIVERED           → { OPENED, BOUNCED }
OPENED              → { CLICKED, REPLIED }
CLICKED             → { REPLIED }
REPLIED             → { MEETING_BOOKED, NURTURING }
MEETING_BOOKED      → { WON, LOST, NURTURING }
NURTURING           → { MEETING_BOOKED, LOST }

Terminal states (no outgoing transitions):
    WON, LOST, UNSUBSCRIBED, BOUNCED, BLOCKED, DISQUALIFIED

Retry paths:
    FAILED → QUEUED (retry send)
    FAILED → DRAFT_CREATED (re-draft)
```

### 2.3 State → Event Bus Mapping

Each outreach state transition should emit a corresponding event on the CRM event bus:

| State Transition | Event Bus Event | Notes |
|-----------------|----------------|-------|
| Any → DISCOVERED | `LeadCreated` | Already exists |
| → RESEARCHING | `ResearchStarted` | New event type needed |
| → RESEARCH_COMPLETED | `ResearchCompleted` | New |
| → QUALIFIED | `LeadQualified` | Already exists |
| → OUTREACH_READY | `OutreachReady` | New |
| → DRAFT_CREATED | `OutreachTriggered` | Already exists (maps to draft creation) |
| → WAITING_APPROVAL | `DraftPendingApproval` | New |
| → APPROVED | `OutreachApproved` | New |
| → QUEUED | `EmailQueued` | New |
| → SENT | `EmailSent` | Already exists |
| → DELIVERED | `EmailDelivered` | New (from webhook) |
| → OPENED | `EmailOpened` | New (from webhook) |
| → CLICKED | `EmailClicked` | New (from webhook) |
| → REPLIED | `ReplyReceived` | Already exists |
| → MEETING_BOOKED | `MeetingBooked` | New |
| → WON | `DealWon` | New |
| → LOST | `DealLost` | New |
| → BOUNCED | `EmailBounced` | New |
| → UNSUBSCRIBED | `LeadUnsubscribed` | New |

---

## 3. CRM Entity Field Design

### 3.1 Design Principles

1. **Engine-owned vs CRM-owned separation.** Engine writes scores, evidence, and recommendations. CRM writes sales stages, human decisions, and commercial outcomes.
2. **Immutable audit trail.** Every state transition is recorded in `lead_event_log` (already exists) or a new `outreach_activity` entity.
3. **No duplication across entities.** A field lives on exactly one entity — the one that owns the lifecycle event that mutates it.
4. **EspoCRM field naming convention.** All custom fields prefixed with `pe` (Prospecting Engine) or `oa` (Outreach Activity). Avoid prefix collision with existing `pe*` scoring fields.

---

### 3.2 Lead Entity Fields (EspoCRM `Lead`)

These fields describe the **lead-level** outreach state — not the per-email state.

#### 3.2.1 New Outreach Status Fields

| Field | Type | Required | Engine-Writable | Human-Writable | Description |
|-------|------|:--------:|:---------------:|:--------------:|-------------|
| `oaOutreachStatus` | enum | Yes | Yes (import) | Yes | Master outreach lifecycle state. See §3.2.2. |
| `oaOutreachPhase` | enum | Yes | Yes | No | High-level phase: `DISCOVERY`, `QUALIFICATION`, `PREPARATION`, `SENDING`, `DELIVERY`, `REPLY`, `CLOSED`. Derived from `oaOutreachStatus`. |
| `oaLastContactAt` | datetime | No | No | Yes | Timestamp of last outbound email sent |
| `oaLastEngagementAt` | datetime | No | No | No | Timestamp of last open/click/reply (from webhook) |
| `oaNextFollowUpAt` | datetime | No | Yes | Yes | Scheduled next email date. Computed from campaign step interval. |
| `oaActiveCampaignId` | varchar(64) | No | Yes | Yes | Reference to active Campaign |
| `oaTotalEmailsSent` | int | No | No | No | Aggregated count (all sequences) |
| `oaTotalOpens` | int | No | No | No | Total unique opens across all emails |
| `oaTotalClicks` | int | No | No | No | Total unique clicks across all emails |
| `oaEngagementScore` | float | No | No | No | Cumulative engagement weight (0.0–10.0) |
| `oaEngagementTier` | enum | No | No | No | `COLD`, `WARMING`, `WARM`, `HOT` |
| `oaCurrentSequenceStep` | int | No | Yes | No | Which email in the sequence (1–4) |
| `oaBestReplyType` | enum | No | No | No | Best reply received: `POSITIVE`, `NEUTRAL`, `NEGATIVE`, `NO_REPLY` |
| `oaHasReplied` | bool | No | No | No | True if any reply received |
| `oaIsUnsubscribed` | bool | No | No | No | True if unsubscribed/complaint received |
| `oaDoNotPitch` | bool | No | No | Yes | Human override: stop all outreach (mirrors CLAUDE.md `Do_Not_Pitch`) |
| `oaHumanPriority` | enum | No | No | Yes | `P1`, `P2`, `P3`, `P4` — human-controlled (mirrors CLAUDE.md `Human_Priority`) |
| `oaFinalPriority` | enum | No | No | Yes | Human final decision (mirrors CLAUDE.md `Final_Priority`) |

#### 3.2.2 `oaOutreachStatus` Enum Values

```
DISCOVERED
RESEARCHING
RESEARCH_COMPLETED
QUALIFIED
OUTREACH_READY
DRAFT_CREATED
WAITING_APPROVAL
APPROVED
QUEUED
SENT
DELIVERED
OPENED
CLICKED
REPLIED
MEETING_BOOKED
WON
LOST
NURTURING
UNSUBSCRIBED
BOUNCED
BLOCKED
FAILED
DISQUALIFIED
```

#### 3.2.3 `oaEngagementTier` Enum Values

```
COLD       — No email sent or no engagement signal
WARMING    — First open detected
WARM       — Multiple opens (>2) or any click
HOT        — Click + positive reply
```

#### 3.2.4 Existing Fields to Keep

All existing `pe*` fields on Lead remain unchanged. They belong to the **scoring and evidence** domain, not outreach:

- `peQualificationStatus` — **Keep.** This stores the Engine-side qualification (e.g., `OUTREACH_READY`). It is distinct from `oaOutreachStatus` which tracks the full CRM lifecycle.
- `peOpportunityScoreV4`, `peScoreTier`, `peConfidence`, `peEvidenceCoverage`
- `peBestFirstProduct`
- `peEngineVersion`, `peScoreRulesVersion`

**Decision:** `peQualificationStatus` and `oaOutreachStatus` are **separate fields** with different semantics:
- `peQualificationStatus` = Engine judgment ("is this lead worth pursuing?")
- `oaOutreachStatus` = CRM lifecycle ("where is this lead in the outreach funnel?")

---

### 3.3 EmailDraft Entity (New EspoCRM Custom Entity)

This entity tracks **one email draft per outreach attempt**. A Lead can have multiple EmailDrafts (one per sequence step).

#### 3.3.1 Entity Definition

**Entity Name:** `EmailDraft`
**Parent Relationship:** `belongsTo` Lead (one Lead → many EmailDrafts)

#### 3.3.2 Fields

| Field | Type | Required | Engine-Writable | Human-Writable | Description |
|-------|------|:--------:|:---------------:|:--------------:|-------------|
| `name` | varchar(255) | Yes | Yes | Yes | Auto-generated: `{company} — {product} — Email {sequence_index}` |
| `oaSequenceIndex` | int | Yes | Yes | No | Position in sequence: 1, 2, 3, or 4 |
| `oaProduct` | varchar(255) | Yes | Yes | No | Primary product for this email |
| `oaSubject` | text | Yes | Yes | Yes | Email subject line |
| `oaBody` | text | Yes | Yes | Yes | Plain text email body |
| `oaDraftStatus` | enum | Yes | Yes | Yes | See §3.3.3 |
| `oaSentAt` | datetime | No | No | No | When actually sent (from provider) |
| `oaDeliveredAt` | datetime | No | No | No | When delivery confirmed (webhook) |
| `oaFirstOpenedAt` | datetime | No | No | No | First open timestamp (webhook) |
| `oaLastOpenedAt` | datetime | No | No | No | Most recent open (webhook) |
| `oaClickedAt` | datetime | No | No | No | First click timestamp (webhook) |
| `oaRepliedAt` | datetime | No | No | No | Reply timestamp (webhook or manual) |
| `oaReplyType` | enum | No | No | No | `POSITIVE`, `NEUTRAL`, `NEGATIVE` |
| `oaReplyText` | text | No | No | Yes | Reply body (if captured) |
| `oaOpenCount` | int | No | No | No | Total unique opens |
| `oaClickCount` | int | No | No | No | Total unique clicks |
| `oaProviderMessageId` | varchar(255) | No | No | No | Brevo/SMTP message ID for webhook matching |
| `oaProviderStatus` | varchar(64) | No | No | No | Last known provider status |
| `oaQualityNotes` | text | No | Yes | No | Engine-generated draft quality notes |
| `oaRiskFlags` | jsonArray | No | Yes | No | Validation flags from draft generation |
| `oaApprovedBy` | varchar(255) | No | No | Yes | Who approved this draft |
| `oaApprovedAt` | datetime | No | No | Yes | When approved |
| `oaGeneratedBy` | varchar(64) | No | Yes | No | `rule_based` or `deepseek` |

#### 3.3.3 `oaDraftStatus` Enum Values

```
DRAFT           — Generated but not yet reviewed
READY_FOR_REVIEW — Draft complete, awaiting human review
NEEDS_REVISION  — Human requested changes
APPROVED        — Human approved for sending
QUEUED          — In send queue
SENDING         — Sending in progress (provider accepted)
SENT            — Provider confirmed send (but delivery unknown)
DELIVERED       — Delivery confirmed via webhook
OPENED          — At least one open detected
CLICKED         — At least one click detected
REPLIED         — Reply received
BOUNCED         — Hard/soft bounce
BLOCKED         — Blocked by provider
FAILED          — Send failed (retryable)
CANCELLED       — Human cancelled before sending
```

#### 3.3.4 Relationship to `email_drafts` (PostgreSQL)

The existing `email_drafts` table in PostgreSQL maps roughly to this entity but is missing field structure. The new `EmailDraft` entity should:

1. Absorb and extend `email_drafts`
2. Absorb the tracking fields currently on `email_drafts` (`opens_count`, `clicks_count`, `first_opened_at`)
3. Absorb relevant columns from `email_outreach` (`email_index`, `follow_up_date`)

---

### 3.4 Campaign Entity (New EspoCRM Custom Entity)

This entity represents a **multi-step outreach sequence** for one Lead.

#### 3.4.1 Entity Definition

**Entity Name:** `OutreachCampaign`
**Parent Relationship:** `belongsTo` Lead (one Lead → one active Campaign at a time)
**Note:** A Lead can have multiple historical Campaigns, but only one active.

#### 3.4.2 Fields

| Field | Type | Required | Engine-Writable | Human-Writable | Description |
|-------|------|:--------:|:---------------:|:--------------:|-------------|
| `name` | varchar(255) | Yes | Yes | Yes | `{company} — {product} — {tier} outreach` |
| `oaCampaignStatus` | enum | Yes | Yes | Yes | See §3.4.3 |
| `oaValueTier` | enum | Yes | Yes | No | `HIGH`, `MEDIUM`, `LOW` — from campaign strategy engine |
| `oaTotalSteps` | int | Yes | Yes | No | 2, 3, or 4 based on tier |
| `oaCurrentStep` | int | Yes | Yes | No | Current step number (0 = not started) |
| `oaStepIntervalDays` | jsonArray | Yes | Yes | Yes | `[0, 5, 12]` — days between steps |
| `oaPrimaryProduct` | varchar(255) | Yes | Yes | No | Email 1 product |
| `oaSecondaryProduct` | varchar(255) | No | Yes | No | Email 2 product |
| `oaThirdProduct` | varchar(255) | No | Yes | No | Email 3 product |
| `oaTone` | enum | Yes | Yes | No | `DIRECT`, `PROFESSIONAL`, `LIGHT` |
| `oaStartedAt` | datetime | No | No | No | When campaign was activated |
| `oaCompletedAt` | datetime | No | No | No | When all steps sent or campaign ended |
| `oaPausedAt` | datetime | No | No | Yes | When paused |
| `oaOutcome` | enum | No | No | Yes | `WON`, `LOST`, `NO_RESPONSE`, `UNSUBSCRIBED`, `CANCELLED` |

#### 3.4.3 `oaCampaignStatus` Enum Values

```
DRAFT       — Created but not yet activated
ACTIVE      — Currently sending steps
PAUSED      — Temporarily paused by human
COMPLETED   — All steps sent
CANCELLED   — Terminated before completion
```

#### 3.4.4 Relationship to `campaign_sequences` (PostgreSQL)

The existing `campaign_sequences` table is the database-side representation of this entity. The `OutreachCampaign` EspoCRM entity would sync from it.

---

### 3.5 OutreachActivity Entity (New EspoCRM Custom Entity)

This is the **immutable event timeline** entity — the CRM-side equivalent of `lead_event_log` but scoped to outreach events only.

#### 3.5.1 Entity Definition

**Entity Name:** `OutreachActivity`
**Parent Relationship:** `belongsTo` Lead
**Optional Links:** `belongsTo` EmailDraft, `belongsTo` OutreachCampaign

#### 3.5.2 Fields

| Field | Type | Required | Writable | Description |
|-------|------|:--------:|:--------:|-------------|
| `name` | varchar(255) | Yes | Auto | `{eventType} — {lead.company} — {timestamp}` |
| `oaActivityType` | enum | Yes | No | See §3.5.3 |
| `oaDirection` | enum | Yes | No | `OUTBOUND`, `INBOUND`, `SYSTEM` |
| `oaChannel` | enum | Yes | No | `EMAIL`, `PHONE`, `LINKEDIN`, `WEB_FORM`, `MANUAL` |
| `oaSubject` | varchar(500) | No | No | Email subject (for email activities) |
| `oaBodyPreview` | text | No | No | First 500 chars of body |
| `oaPerformedAt` | datetime | Yes | No | When the activity actually happened |
| `oaProviderEventId` | varchar(255) | No | No | Webhook event ID for dedup |
| `oaProviderRaw` | jsonObject | No | No | Full webhook payload (for audit) |
| `oaSignalWeight` | float | No | No | Engagement score delta |
| `oaMetadata` | jsonObject | No | No | Extensible context dict |

#### 3.5.3 `oaActivityType` Enum Values

```
EMAIL_SENT
EMAIL_DELIVERED
EMAIL_OPENED
EMAIL_CLICKED
EMAIL_BOUNCED
EMAIL_BLOCKED
EMAIL_FAILED
EMAIL_REPLIED
MEETING_BOOKED
DEAL_WON
DEAL_LOST
LEAD_UNSUBSCRIBED
LEAD_DISQUALIFIED
STATUS_CHANGED
NOTE_ADDED
DRAFT_APPROVED
DRAFT_REJECTED
CAMPAIGN_ACTIVATED
CAMPAIGN_PAUSED
CAMPAIGN_COMPLETED
CAMPAIGN_CANCELLED
```

---

### 3.6 Complete Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────────┐
│      Lead        │1────N│   ResearchEvidence    │ (existing)
│                  │       └──────────────────────┘
│ oaOutreachStatus │
│ oaEngagementTier │       ┌──────────────────────┐
│ oaNextFollowUpAt │1────N│     EmailDraft        │ (new)
│ oaActiveCampaign │       │                      │
│ ...              │       │ oaDraftStatus        │
└────────┬─────────┘       │ oaSequenceIndex      │
         │                 │ oaSentAt             │
         │                 │ oaOpenedAt           │
         │                 │ oaRepliedAt          │
         │1                │ ...                  │
         │                 └──────────┬───────────┘
         │                            │N
┌────────▼─────────┐                 │
│ OutreachCampaign │1────N───────────┘ (one campaign
│                  │                     has N drafts)
│ oaCampaignStatus │
│ oaValueTier      │       ┌──────────────────────┐
│ oaCurrentStep    │1────N│  OutreachActivity     │ (new)
│ ...              │       │                      │
└──────────────────┘       │ oaActivityType       │
                           │ oaDirection          │
                           │ ...                  │
                           └──────────────────────┘
```

**Design Note:** `OutreachActivity` can link to either `Lead` directly, or `Lead` + `EmailDraft`, or `Lead` + `OutreachCampaign`, depending on the activity type. This is flexible linking — EspoCRM supports multiple parent relationships on custom entities.

---

## 4. Field-to-Entity Ownership Analysis

### 4.1 Guiding Questions

For each field, ask:

1. **Which entity's lifecycle event mutates this field?** → The field belongs there.
2. **What is the cardinality?** One-per-lead → Lead. One-per-email → EmailDraft.
3. **Who needs to query it?** Sales ops dashboard → aggregated on Lead. Email performance → on EmailDraft.
4. **Is it immutable after write?** → Belongs on Activity, not the parent entity.

### 4.2 Field Ownership Decision Matrix

#### 4.2.1 Fields that live on **Lead**

These fields describe the **aggregate state** of the lead's outreach journey. They are mutated by aggregated events across multiple emails.

| Field | Rationale |
|-------|----------|
| `oaOutreachStatus` | Single source of truth for "where is this lead?" Updated by the latest significant event. |
| `oaOutreachPhase` | Derived from status — convenience for dashboard filtering. |
| `oaLastContactAt` | Aggregated: max sent_at across all EmailDrafts. |
| `oaLastEngagementAt` | Aggregated: max opened_at/clicked_at/replied_at across all EmailDrafts. |
| `oaNextFollowUpAt` | Computed from active Campaign step interval. |
| `oaActiveCampaignId` | Pointer to the current campaign — needed for quick access. |
| `oaTotalEmailsSent` | COUNT of EmailDrafts with oaDraftStatus ≥ SENT. |
| `oaTotalOpens` | SUM of oaOpenCount across all EmailDrafts. |
| `oaTotalClicks` | SUM of oaClickCount across all EmailDrafts. |
| `oaEngagementScore` | SUM of oaSignalWeight across all OutreachActivity records. |
| `oaEngagementTier` | Derived from oaEngagementScore + oaHasReplied. |
| `oaCurrentSequenceStep` | From active Campaign.currentStep. |
| `oaBestReplyType` | MAX() of oaReplyType across all EmailDrafts. |
| `oaHasReplied` | EXISTS any EmailDraft with oaRepliedAt IS NOT NULL. |
| `oaIsUnsubscribed` | EXISTS any OutreachActivity with type LEAD_UNSUBSCRIBED. |
| `oaDoNotPitch` | Human override flag — must be on Lead for quick dashboard filter. |
| `oaHumanPriority` | Human-owned — must be on Lead for dashboard sorting. |
| `oaFinalPriority` | Human-owned — must be on Lead. |

#### 4.2.2 Fields that live on **EmailDraft**

These fields describe **one specific email** — sent or unsent. They are mutated by events tied to a single message.

| Field | Rationale |
|-------|----------|
| `oaSequenceIndex` | Per-email position. |
| `oaProduct` | Each email can have a different product (per MULTI_PRODUCT_OUTREACH_RULE). |
| `oaSubject` | Per-email. |
| `oaBody` | Per-email. |
| `oaDraftStatus` | Per-email lifecycle. |
| `oaSentAt` | When THIS email was sent. |
| `oaDeliveredAt` | Delivery confirmation for THIS email. |
| `oaFirstOpenedAt` | First open of THIS email. |
| `oaLastOpenedAt` | Most recent open of THIS email. |
| `oaClickedAt` | First click on THIS email. |
| `oaRepliedAt` | Reply to THIS email. |
| `oaReplyType` | Classification of THIS email's reply. |
| `oaReplyText` | Reply body for THIS email. |
| `oaOpenCount` | Open count for THIS email. |
| `oaClickCount` | Click count for THIS email. |
| `oaProviderMessageId` | Unique ID for this specific send. |
| `oaProviderStatus` | Provider status for this specific send. |
| `oaQualityNotes` | Draft generation notes for this email. |
| `oaRiskFlags` | Validation flags for this email. |
| `oaApprovedBy` | Who approved this email. |
| `oaApprovedAt` | When this email was approved. |

#### 4.2.3 Fields that live on **OutreachCampaign**

These fields describe the **multi-step sequence** configuration and state.

| Field | Rationale |
|-------|----------|
| `oaCampaignStatus` | Campaign-level lifecycle. |
| `oaValueTier` | Strategy parameter — same for all steps. |
| `oaTotalSteps` | Campaign configuration. |
| `oaCurrentStep` | Campaign progress. |
| `oaStepIntervalDays` | Scheduling configuration. |
| `oaPrimaryProduct` / `oaSecondaryProduct` / `oaThirdProduct` | Product rotation plan per CLAUDE.md §10. |
| `oaTone` | Campaign-level tone setting. |
| `oaStartedAt` / `oaCompletedAt` / `oaPausedAt` | Campaign lifecycle timestamps. |
| `oaOutcome` | Campaign result. |

#### 4.2.4 Fields that live on **OutreachActivity**

These fields are **immutable event records** — they document what happened at a point in time.

| Field | Rationale |
|-------|----------|
| `oaActivityType` | What happened. |
| `oaDirection` | Outbound vs inbound vs system. |
| `oaChannel` | Which channel. |
| `oaSubject` | Snapshot of subject at the time. |
| `oaBodyPreview` | Snapshot of body at time. |
| `oaPerformedAt` | When it happened. |
| `oaProviderEventId` | Dedup key. |
| `oaProviderRaw` | Full audit payload. |
| `oaSignalWeight` | Engagement impact of this event. |
| `oaMetadata` | Extensible context. |

### 4.3 What Happens to Existing Database Tables

| Current Table | Future State | Migration Approach |
|--------------|-------------|-------------------|
| `leads` (outreach columns) | Fields migrate to EspoCRM Lead entity | Read from `leads` → write to EspoCRM `Lead.oa*` fields |
| `email_drafts` | Replaced by EmailDraft entity | Map columns to EmailDraft fields |
| `email_outreach` | Absorbed into EmailDraft + OutreachCampaign | `email_index` → EmailDraft.oaSequenceIndex; sequence logic → OutreachCampaign |
| `outreach_queue` | Replaced by EmailDraft.oaDraftStatus = QUEUED | Status field migration |
| `send_queue` | Absorbed into EmailDraft status workflow | Simplify to EmailDraft |
| `email_log` | Replaced by EmailDraft delivery fields + OutreachActivity | Outbound audit moves to Activity |
| `email_reply_log` | Absorbed into EmailDraft reply fields + OutreachActivity | Reply data lives on EmailDraft; event on Activity |
| `outreach_events` | Replaced by OutreachActivity | Raw events → Activity records |
| `follow_up_queue` | Replaced by OutreachCampaign step scheduling | Campaign engine handles follow-up |
| `email_events` (Brevo raw) | Replaced by OutreachActivity (filtered) | Webhook → Activity; raw payload optional |
| `campaign_sequences` | Replaced by OutreachCampaign entity | Direct mapping |
| `lead_event_log` | **Keep.** Used by OutreachActivity as source of truth for non-outreach events | OutreachActivity is a CRM-facing subset |

---

## 5. Implementation Recommendations

### 5.1 Implementation Order (Phased)

#### Phase 1: EspoCRM Schema Extension (no code changes)

1. Add `oaOutreachStatus` enum field to Lead entity
2. Add all `oa*` aggregate fields to Lead entity (§3.2.1)
3. Create `EmailDraft` custom entity with all fields (§3.3)
4. Create `OutreachCampaign` custom entity with all fields (§3.4)
5. Create `OutreachActivity` custom entity with all fields (§3.5)
6. Deploy updated extension to EspoCRM instance
7. **Validate:** All entities visible in EspoCRM admin. No data populated yet.

#### Phase 2: Engine → EspoCRM Sync (new fields)

1. Extend `integration/espocrm_sync/contract.py` to include `oaOutreachStatus = "DISCOVERED"` in the sync payload
2. Extend `integration/espocrm_sync/mapper.py` to map engine state → `oaOutreachStatus`
3. **Validate:** Newly synced leads appear with `oaOutreachStatus = DISCOVERED`

#### Phase 3: Email Draft Sync

1. When `event_handlers.py` creates an `email_drafts` row, also create/update an `EmailDraft` record in EspoCRM
2. Map `email_drafts` columns → EmailDraft entity fields
3. **Validate:** Drafts visible in EspoCRM linked to their Lead

#### Phase 4: Campaign Sync

1. When `campaign_strategy.py` builds a Campaign, create an `OutreachCampaign` record in EspoCRM
2. Link to the Lead via `oaActiveCampaignId`
3. **Validate:** Campaigns visible in EspoCRM with step configuration

#### Phase 5: Webhook → Activity Sync

1. Extend `brevo_webhook_handler.py` to create `OutreachActivity` records in EspoCRM for each classified event
2. Update corresponding `EmailDraft` delivery fields (oaSentAt, oaOpenedAt, etc.)
3. Update Lead aggregate fields (oaLastEngagementAt, oaEngagementScore, etc.)
4. **Validate:** Email delivery timeline visible in EspoCRM per Lead

#### Phase 6: State Transition Engine

1. Implement `oaOutreachStatus` state machine as a standalone module
2. Wire into `event_handlers.py` — each event handler updates `oaOutreachStatus` on the EspoCRM Lead
3. Implement validation: reject invalid transitions; log to `OutreachActivity` with type `STATUS_CHANGED`
4. **Validate:** Each Lead's `oaOutreachStatus` correctly reflects its actual state

#### Phase 7: Dashboard & Views

1. Build EspoCRM list views filtered by `oaOutreachStatus`
2. Build kanban board grouped by `oaOutreachPhase`
3. Build email performance dashboard (open rate, click rate, reply rate per campaign)
4. **Validate:** Sales ops can manage pipeline entirely from EspoCRM

### 5.2 Boundary Rules (Engine vs CRM)

These rules must be enforced in the sync adapter:

```
┌──────────────────────────────────────────────────────────────┐
│  ENGINE WRITES                    │  CRM WRITES              │
├───────────────────────────────────┼──────────────────────────┤
│  peQualificationStatus            │  oaOutreachStatus        │
│  peOpportunityScoreV4             │  oaDoNotPitch            │
│  peScoreTier                      │  oaHumanPriority         │
│  peBestFirstProduct               │  oaFinalPriority         │
│  peConfidence                     │  oaApprovedBy            │
│  peEvidenceCoverage               │  oaApprovedAt            │
│  EmailDraft.oaSubject (initial)   │  EmailDraft.oaSubject    │
│  EmailDraft.oaBody (initial)      │     (after human edit)   │
│  EmailDraft.oaQualityNotes        │  EmailDraft.oaBody       │
│  EmailDraft.oaGeneratedBy         │     (after human edit)   │
│  OutreachCampaign (full config)   │  OutreachCampaign        │
│                                   │     .oaCampaignStatus    │
│                                   │     (ACTIVE → PAUSED →   │
│                                   │      CANCELLED only)     │
│  OutreachActivity (system         │  OutreachActivity        │
│    events only — EMAIL_*,         │    (NOTE_ADDED,          │
│    LEAD_DISQUALIFIED,             │     MEETING_BOOKED,      │
│    STATUS_CHANGED)                │     DEAL_WON, DEAL_LOST) │
└───────────────────────────────────┴──────────────────────────┘
```

### 5.3 Data Population Strategy

**Do not backfill historical data initially.** The new fields start empty for existing leads. Only leads that pass through the new pipeline get populated.

For historical reporting, the existing PostgreSQL tables (`email_log`, `email_reply_log`, `lead_event_log`) remain the source of truth until a migration script is explicitly requested and approved.

### 5.4 Field Naming Convention

| Prefix | Scope | Owner |
|--------|-------|-------|
| `pe` | Prospecting Engine — scoring, evidence, qualification | Engine |
| `oa` | Outreach Activity — email lifecycle, campaigns, replies | CRM (engine writes initial values, CRM mutates) |
| (no prefix) | Standard EspoCRM fields (`name`, `website`, `status`) | EspoCRM |

**Existing `pe*` fields are NOT renamed.** The `oa` prefix is new and applies only to outreach fields.

### 5.5 Integration with CLAUDE.md Rules

This status model directly supports key CLAUDE.md requirements:

| CLAUDE.md Rule | How the Model Supports It |
|---------------|--------------------------|
| **3-email sequence** (Email 1 → 2 → 3) | `OutreachCampaign.oaTotalSteps` + `EmailDraft.oaSequenceIndex` |
| **Primary/Secondary/Third product rotation** | `OutreachCampaign.oaPrimaryProduct` / `oaSecondaryProduct` / `oaThirdProduct` |
| **Do_Not_Pitch override** | `Lead.oaDoNotPitch` — checked before any send |
| **Human_Priority / Final_Priority** | `Lead.oaHumanPriority` / `Lead.oaFinalPriority` — human-only fields |
| **Best_First_Product seeds Primary only** | `EmailDraft.oaProduct` can differ from `Lead.peBestFirstProduct` |
| **No auto-send** | `EmailDraft.oaDraftStatus` must transition through `APPROVED` |
| **Reply tracking** | `EmailDraft.oaRepliedAt` + `Lead.oaHasReplied` + `OutreachActivity` |

### 5.6 Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Three existing state systems drift further during implementation | Phase 6 state transition engine becomes the single writer; existing systems become readers only |
| EspoCRM API rate limits with frequent webhook updates | Batch OutreachActivity creation; use EspoCRM bulk API; update Lead aggregates no more than once per minute |
| Field proliferation makes Lead entity too wide | Use EspoCRM side panels / tabbed detail views; aggregate fields are computed, not all displayed |
| Human and engine writes conflict on same field | Strict ownership rules in §5.2; sync adapter enforces them |

---

## 6. Gap Summary

### 6.1 What Exists Today

| Capability | Current State |
|-----------|--------------|
| Lead qualification status | `peQualificationStatus` (varchar, single value) |
| Email draft storage | `email_drafts` table + `email_outreach` table (overlapping) |
| Send queue | `outreach_queue` + `send_queue` (two separate queues) |
| Delivery tracking | Brevo webhook → `email_events` + `brevo_webhook_handler.py` |
| Reply tracking | `email_reply_log` + `feedback_signals` |
| Campaign strategy | `campaign_strategy.py` + `campaign_sequences` table |
| Event timeline | `lead_event_log` (10 event types) |
| Engagement scoring | `brevo_webhook_handler.py` (computes `engagement_status` + `engagement_score`) |
| Follow-up scheduling | `follow_up_queue` table |

### 6.2 What's Missing

| Gap | Impact |
|-----|--------|
| **No unified outreach status on Lead** | Can't filter EspoCRM by "all leads awaiting reply" or "all bounced leads" |
| **No EmailDraft entity in CRM** | Can't see which email was sent when, or what it said, from EspoCRM |
| **No Campaign entity in CRM** | Can't see that a lead is on Email 2 of 3, or what product is next |
| **No Activity timeline in CRM** | Can't see the full outreach history (sent → delivered → opened → clicked → replied) in one view |
| **No human approval gate in CRM** | Draft approval is implicit; no explicit `WAITING_APPROVAL` state |
| **No WON/LOST tracking** | Can't measure conversion rate from the CRM |
| **No unsubscribe/block management** | `BLOCKED` and `UNSUBSCRIBED` exist in DB but not visible in EspoCRM |
| **Three separate state systems** | Engine state machine, DB pipeline_stage, and event bus don't share a unified schema |
| **No engagement tier on Lead** | `engagement_status` exists in DB but not synced to EspoCRM |

### 6.3 What This Design Resolves

This document provides:

1. **A single unified outreach lifecycle** (§2) that spans Engine → CRM → Email Provider → Reply
2. **Four CRM entities** (Lead extension + 3 new custom entities) that together model the full outreach funnel
3. **Clear field ownership** (§4) — no ambiguity about which entity owns which field
4. **Implementation phases** (§5.1) — phased rollout that can start with schema-only changes
5. **Engine vs CRM boundary rules** (§5.2) — preventing write conflicts
6. **CLAUDE.md compliance** (§5.5) — the model supports all current business rules

---

## Appendix A: Field Quick Reference

### Lead `oa*` Fields (20 fields)

```
oaOutreachStatus       oaOutreachPhase        oaLastContactAt
oaLastEngagementAt     oaNextFollowUpAt       oaActiveCampaignId
oaTotalEmailsSent      oaTotalOpens           oaTotalClicks
oaEngagementScore      oaEngagementTier       oaCurrentSequenceStep
oaBestReplyType        oaHasReplied           oaIsUnsubscribed
oaDoNotPitch           oaHumanPriority        oaFinalPriority
```

### EmailDraft Fields (21 fields)

```
name                   oaSequenceIndex        oaProduct
oaSubject              oaBody                 oaDraftStatus
oaSentAt               oaDeliveredAt          oaFirstOpenedAt
oaLastOpenedAt         oaClickedAt            oaRepliedAt
oaReplyType            oaReplyText            oaOpenCount
oaClickCount           oaProviderMessageId    oaProviderStatus
oaQualityNotes         oaRiskFlags            oaApprovedBy
oaApprovedAt           oaGeneratedBy
```

### OutreachCampaign Fields (15 fields)

```
name                   oaCampaignStatus       oaValueTier
oaTotalSteps           oaCurrentStep          oaStepIntervalDays
oaPrimaryProduct       oaSecondaryProduct     oaThirdProduct
oaTone                 oaStartedAt            oaCompletedAt
oaPausedAt             oaOutcome
```

### OutreachActivity Fields (12 fields)

```
name                   oaActivityType         oaDirection
oaChannel              oaSubject              oaBodyPreview
oaPerformedAt          oaProviderEventId      oaProviderRaw
oaSignalWeight         oaMetadata
```

---

## Appendix B: State Transition Reference Implementation (Pseudocode)

```python
# Conceptual — NOT production code. For design illustration only.

from enum import StrEnum

class OutreachStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    RESEARCHING = "RESEARCHING"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    QUALIFIED = "QUALIFIED"
    OUTREACH_READY = "OUTREACH_READY"
    DRAFT_CREATED = "DRAFT_CREATED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"
    REPLIED = "REPLIED"
    MEETING_BOOKED = "MEETING_BOOKED"
    WON = "WON"
    LOST = "LOST"
    NURTURING = "NURTURING"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    BOUNCED = "BOUNCED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    DISQUALIFIED = "DISQUALIFIED"

TRANSITIONS: dict[OutreachStatus, set[OutreachStatus]] = {
    OutreachStatus.DISCOVERED:         {OutreachStatus.RESEARCHING, OutreachStatus.DISQUALIFIED},
    OutreachStatus.RESEARCHING:        {OutreachStatus.RESEARCH_COMPLETED, OutreachStatus.DISQUALIFIED},
    OutreachStatus.RESEARCH_COMPLETED: {OutreachStatus.QUALIFIED, OutreachStatus.DISQUALIFIED},
    OutreachStatus.QUALIFIED:          {OutreachStatus.OUTREACH_READY, OutreachStatus.DISQUALIFIED},
    OutreachStatus.OUTREACH_READY:     {OutreachStatus.DRAFT_CREATED, OutreachStatus.DISQUALIFIED},
    OutreachStatus.DRAFT_CREATED:      {OutreachStatus.WAITING_APPROVAL, OutreachStatus.OUTREACH_READY},
    OutreachStatus.WAITING_APPROVAL:   {OutreachStatus.APPROVED, OutreachStatus.DRAFT_CREATED, OutreachStatus.DISQUALIFIED},
    OutreachStatus.APPROVED:           {OutreachStatus.QUEUED, OutreachStatus.WAITING_APPROVAL},
    OutreachStatus.QUEUED:             {OutreachStatus.SENT, OutreachStatus.FAILED},
    OutreachStatus.SENT:               {OutreachStatus.DELIVERED, OutreachStatus.BOUNCED, OutreachStatus.BLOCKED, OutreachStatus.FAILED},
    OutreachStatus.DELIVERED:          {OutreachStatus.OPENED, OutreachStatus.BOUNCED},
    OutreachStatus.OPENED:             {OutreachStatus.CLICKED, OutreachStatus.REPLIED},
    OutreachStatus.CLICKED:            {OutreachStatus.REPLIED},
    OutreachStatus.REPLIED:            {OutreachStatus.MEETING_BOOKED, OutreachStatus.NURTURING},
    OutreachStatus.MEETING_BOOKED:     {OutreachStatus.WON, OutreachStatus.LOST, OutreachStatus.NURTURING},
    OutreachStatus.NURTURING:          {OutreachStatus.MEETING_BOOKED, OutreachStatus.LOST},
    OutreachStatus.FAILED:             {OutreachStatus.QUEUED, OutreachStatus.DRAFT_CREATED},
    # Terminal states:
    OutreachStatus.WON:           set(),
    OutreachStatus.LOST:          set(),
    OutreachStatus.UNSUBSCRIBED:  set(),
    OutreachStatus.BOUNCED:       set(),
    OutreachStatus.BLOCKED:       set(),
    OutreachStatus.DISQUALIFIED:  set(),
}

TERMINAL_STATES = {
    OutreachStatus.WON, OutreachStatus.LOST, OutreachStatus.UNSUBSCRIBED,
    OutreachStatus.BOUNCED, OutreachStatus.BLOCKED, OutreachStatus.DISQUALIFIED,
}

def compute_phase(status: OutreachStatus) -> str:
    """Derive the high-level phase from the detailed status."""
    if status in {OutreachStatus.DISCOVERED, OutreachStatus.RESEARCHING,
                  OutreachStatus.RESEARCH_COMPLETED}:
        return "DISCOVERY"
    if status in {OutreachStatus.QUALIFIED}:
        return "QUALIFICATION"
    if status in {OutreachStatus.OUTREACH_READY, OutreachStatus.DRAFT_CREATED,
                  OutreachStatus.WAITING_APPROVAL, OutreachStatus.APPROVED}:
        return "PREPARATION"
    if status in {OutreachStatus.QUEUED, OutreachStatus.SENT}:
        return "SENDING"
    if status in {OutreachStatus.DELIVERED, OutreachStatus.OPENED,
                  OutreachStatus.CLICKED}:
        return "DELIVERY"
    if status in {OutreachStatus.REPLIED, OutreachStatus.MEETING_BOOKED}:
        return "REPLY"
    if status in {OutreachStatus.WON, OutreachStatus.LOST,
                  OutreachStatus.NURTURING}:
        return "CLOSED"
    return "UNKNOWN"
```

---

*End of document. For questions, refer to `CLAUDE.md` for business rules and `ESPOCRM_ENTITY_MAPPING_DESIGN_V1.md` for the existing entity mapping.*
