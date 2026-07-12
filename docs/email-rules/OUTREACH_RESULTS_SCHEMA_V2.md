# Outreach Results Schema V2

> Created: 2026-06-09
> Purpose: CRM data model for the full dealer-development lifecycle. Tracks from first contact through conversion, not just email replies.
> Reference: `PROJECT_STATE_2026_06_09.md` for product hierarchy, dealer classification, and outreach rules.

---

## 1. Design Philosophy

The goal is not to track emails.

The goal is to track dealer development.

A dealer may take 30 days, 90 days, or 180 days to convert. The system must preserve relationship history across that entire window.

Every state change must be traceable. Every field must have a clear owner: system-generated or human-controlled.

---

## 2. Control Boundary

| Field Category | Owner | Rule |
|---------------|-------|------|
| Identifiers | System + Human | Set once at discovery; updated if company changes |
| Relationship status | **Human only** | AI may suggest; human confirms |
| Product tracking | Mixed | Best_First_Product = system-suggested; Current/Potential = human-controlled |
| Outreach activity | System | Auto-populated from email generation and sending |
| Reply tracking | System + Human | Reply_Status auto-detected where possible; human confirms |
| Interest level | **Human only** | Judgment call based on reply content |
| Commercial signals | **Human only** | Based on actual dealer requests |
| Follow-up | Mixed | System suggests; human confirms |
| Outcome | **Human only** | Final disposition |
| Notes | **Human only** | Free text |

**Invariant:** `Relationship_Status`, `Outcome`, and `Current_Cooperation_Products` are authoritative human-controlled fields. The system may propose values but must not write them without human confirmation.

---

## 3. Unique Identifiers

Set at dealer discovery. Do not change after creation unless the company legally changes name or domain.

| Field | Type | Required | Description |
|-------|------|:---:|------|
| `Dealer_ID` | string | Y | Unique identifier. Format: `ISO2-XXXX` (e.g., `GB-0001`, `CA-0015`) |
| `Company_Name` | string | Y | Normalized company name |
| `Domain` | string | Y | Primary domain, lowercase, no protocol |
| `Country` | string | Y | ISO 3166-1 alpha-2 country code |
| `Dealer_Class` | enum | Y | `A`, `B`, or `C` (Class C excluded from outreach) |
| `Dealer_Tags` | string[] | Y | From approved tag list (see Section 4) |

### Dealer_ID Convention

```
ISO2-NNNN

Examples:
GB-0001  (Solid Print3D, United Kingdom)
CA-0015  (Digit Makers, Canada)
DE-0003  (3Dmensionals, Germany)
FR-0002  (Makershop, France)
AU-0012  (3D BRO, Australia)
```

Assign sequentially within country. Never reuse deleted IDs.

---

## 4. Dealer Tags

Controlled vocabulary from `SCORING_ENGINE_V3_1_PATCH.md`. Multiple tags allowed.

| Tag | Meaning |
|-----|---------|
| `Bambu` | Bambu Lab ecosystem dealer |
| `Resin` | Resin printer ecosystem |
| `FDM` | FDM printer ecosystem |
| `PrintFarm` | Serves print farm customers |
| `Service` | Repair, maintenance, or service business |
| `Education` | Serves schools, universities, labs |
| `Industrial` | Serves industrial/manufacturing customers |
| `Dental` | Serves dental/lab customers |
| `Materials` | Filament or resin materials focus |
| `Accessories` | Parts, accessories, add-ons focus |

Tags are metadata. They do not directly modify scores. They enable filtering, segmentation, and reporting.

---

## 5. Relationship Status

**Human-controlled.** Tracks the current state of the dealer relationship.

| Status | Meaning | Typical Trigger |
|--------|---------|-----------------|
| `New Prospect` | Discovered, scored, not yet contacted | Initial discovery and scoring |
| `Contacted` | First outreach sent, awaiting reply | Email 1 sent |
| `Replied` | Dealer responded; content being evaluated | Any reply received |
| `Qualified` | Dealer expressed interest; fit confirmed | Positive reply |
| `Sample Requested` | Dealer asked for sample | Explicit sample request |
| `Sample Sent` | Sample dispatched to dealer | Fulfillment confirmed |
| `Pricing Discussion` | Dealer engaged on pricing | Pricing or MOQ questions |
| `Negotiation` | Active negotiation in progress | Terms discussion |
| `Active Dealer` | Converted; ongoing relationship | First order or agreement |
| `Dormant Dealer` | Was active; no recent activity | 6+ months no engagement |
| `Do Not Pitch` | Blocked from outreach | Human override, competitor, irrelevant |

### State Transitions

```
New Prospect ──→ Contacted ──→ Replied ──→ Qualified ──→ Sample Requested
                    │              │            │              │
                    │              │            │              └──→ Sample Sent
                    │              │            │                      │
                    │              │            │                      └──→ Pricing Discussion
                    │              │            │                              │
                    │              │            │                              └──→ Negotiation ──→ Active Dealer
                    │              │            │
                    │              │            └──→ Dormant Dealer (no activity)
                    │              │
                    │              └──→ Do Not Pitch (negative reply, competitor, irrelevant)
                    │
                    └──→ Do Not Pitch (bounce, wrong contact, no path forward)
```

Any state can transition to `Do Not Pitch` or `Dormant Dealer`.

---

## 6. Product Tracking

### Current_Cooperation_Products

Products the dealer already purchases or carries from Chitu Systems. **Human-controlled.**

Multiple values allowed. Use approved product names:

```
LCD Screen
PlateCycler
Resin Tank
Filament Dryer
Heater
Resin
Filament
Mainboard
Light Source
Software
UV Meter
```

### Potential_Cooperation_Products

Products the dealer could expand into. **Human-controlled** with system suggestions.

Multiple values allowed. Same product name list.

### Best_First_Product

System-suggested entry product based on evidence scoring. Single value from Tier 1 or Tier 2 (Heater). Set during opportunity scoring and updated when evidence changes or human review overrides.

---

## 7. Outreach Tracking

System-populated from email generation workflow.

| Field | Type | Required | Description |
|-------|------|:---:|------|
| `Email_Sent` | boolean | Y | `Yes` / `No` |
| `First_Email_Date` | date | N | Date of first outreach email |
| `Last_Email_Date` | date | N | Date of most recent outreach email |
| `Email_Version` | string | N | Template version used (e.g., `V4.5`, `V4.6`) |
| `Email_Count` | integer | Y | Total outreach emails sent to this dealer |

### Email_Version Values

Controlled vocabulary. Current versions:

```
V4.5
V4.6
```

Add new versions as templates evolve. Do not delete old values — they preserve what was sent.

---

## 8. Reply Tracking

### Reply_Status

| Status | Meaning |
|--------|---------|
| `No Reply` | No response received |
| `Auto Reply` | Out-of-office or automated response |
| `Replied` | Human reply received; content neutral or unclear |
| `Interested` | Reply expresses interest |
| `Not Interested` | Reply declines; no path forward now |
| `Wrong Contact` | Reply indicates wrong person/department |
| `Forwarded Internally` | Was told it was forwarded to another person |

### Reply_Date

Date of first reply received. Null if no reply.

### Response_Time_Days

Calculated: `Reply_Date - First_Email_Date`. Null if no reply.

---

## 9. Interest Level

**Human-controlled.** Set after evaluating reply content. Judgment call.

| Level | Meaning | Typical Signal |
|-------|---------|----------------|
| `Hot` | Strong interest, likely to convert soon | Asked for pricing, samples, or immediate next step |
| `Warm` | Interested but not urgent | Asked questions, open to more info |
| `Cold` | Minimal or ambiguous interest | Brief reply, "not now," or forwarded without follow-up |

---

## 10. Commercial Signals

**Human-controlled.** Set to `Yes` only when the dealer explicitly requests or asks about each item.

| Field | Type | Description |
|-------|------|-------------|
| `Requested_Pricing` | boolean | Dealer asked for price list or pricing |
| `Requested_Catalog` | boolean | Dealer asked for product catalog or line card |
| `Requested_Sample` | boolean | Dealer asked for sample evaluation |
| `Requested_MOQ` | boolean | Dealer asked about minimum order quantities |
| `Requested_Distributor_Terms` | boolean | Dealer asked about distributor/reseller terms |

These are the leading indicators of deal progression. Track them independently from the relationship status so you can filter and prioritize.

---

## 11. Follow-Up

| Field | Type | Required | Description |
|-------|------|:---:|------|
| `Next_Action` | enum | Y | Next step to take |
| `Next_Action_Date` | date | Y | Date by which the action should be completed |

### Next_Action Values

```
Send Pricing
Send Sample
Send Catalog
Follow Up 7 Days
Follow Up 14 Days
Await Response
Closed
```

System may suggest based on commercial signals (e.g., `Requested_Pricing = Yes` → suggest `Send Pricing`). Human confirms.

---

## 12. Outcome

**Human-controlled.** Final disposition of this dealer opportunity.

| Outcome | Meaning |
|---------|---------|
| `No Response` | No reply after full sequence; closed for now |
| `Nurturing` | Long-term nurture; revisit periodically |
| `Opportunity` | Active opportunity; in pipeline |
| `Sample Stage` | Sample evaluation in progress |
| `Negotiation` | Terms/pricing being discussed |
| `Won` | Converted to active dealer |
| `Lost` | Declined, went with competitor, or no fit |

---

## 13. Notes

### Human_Notes

Free text. Human-controlled.

Use for:
- Context not captured in structured fields
- Dealer-specific observations
- Account history notes
- Reason for `Do Not Pitch` or `Lost` disposition

Do not use for:
- Scoring rationale (that goes in `opportunity_scores`)
- Product evidence (that goes in `evidence_summary`)
- Contact details (that goes in the `contact` object)

---

## 14. Full Record Schema

```jsonc
{
  // ── Identifiers ──
  "Dealer_ID": "GB-0001",
  "Company_Name": "Solid Print3D",
  "Domain": "solidprint3d.co.uk",
  "Country": "GB",
  "Dealer_Class": "A",
  "Dealer_Tags": ["Bambu", "FDM", "Industrial", "Education"],

  // ── Relationship ──
  "Relationship_Status": "New Prospect",

  // ── Product Tracking ──
  "Current_Cooperation_Products": [],
  "Potential_Cooperation_Products": ["PlateCycler", "Filament Dryer"],
  "Best_First_Product": "PlateCycler",

  // ── Outreach ──
  "Email_Sent": "No",
  "First_Email_Date": null,
  "Last_Email_Date": null,
  "Email_Version": null,
  "Email_Count": 0,

  // ── Reply Tracking ──
  "Reply_Status": "No Reply",
  "Reply_Date": null,
  "Response_Time_Days": null,

  // ── Interest Level ──
  "Interest_Level": null,

  // ── Commercial Signals ──
  "Requested_Pricing": "No",
  "Requested_Catalog": "No",
  "Requested_Sample": "No",
  "Requested_MOQ": "No",
  "Requested_Distributor_Terms": "No",

  // ── Follow-Up ──
  "Next_Action": "Follow Up 7 Days",
  "Next_Action_Date": "2026-06-16",

  // ── Results ──
  "Outcome": "Opportunity",

  // ── Notes ──
  "Human_Notes": ""
}
```

---

## 15. Reporting Metrics

Future dashboard should calculate these metrics from the schema fields.

### Funnel Metrics

| Metric | Calculation |
|--------|-------------|
| Emails Sent | Count where `Email_Sent = Yes` |
| Reply Rate | `Replied` + `Interested` + `Not Interested` + `Wrong Contact` + `Forwarded Internally` / `Emails Sent` |
| Positive Reply Rate | `Interested` / `Emails Sent` |
| Sample Request Rate | `Requested_Sample = Yes` / `Emails Sent` |
| Pricing Request Rate | `Requested_Pricing = Yes` / `Emails Sent` |
| Opportunity Rate | `Outcome = Opportunity` / `Emails Sent` |
| Conversion Rate | `Outcome = Won` / `Emails Sent` |

### Dimension Filters

All metrics can be sliced by:

- **Country** — regional performance
- **Product** — which products generate replies
- **Dealer Tag** — which dealer segments convert
- **Dealer Class** — Class A vs Class B performance

### Time-Based Metrics

- Average `Response_Time_Days` (for dealers who replied)
- Average days from `First_Email_Date` to `Outcome = Won`
- Average days in each `Relationship_Status`

---

## 16. Integration Points

### Input From Scoring Engine

When a dealer is scored and approved for outreach:
- `Dealer_ID`, `Company_Name`, `Domain`, `Country`, `Dealer_Class`, `Dealer_Tags` ← from dealer record
- `Best_First_Product` ← from opportunity scoring
- `Potential_Cooperation_Products` ← from opportunity scoring
- `Relationship_Status` ← set to `New Prospect`

### Input From Email Generator

When an email draft is approved and sent:
- `Email_Sent` ← set to `Yes`
- `First_Email_Date` ← set to send date (if first email)
- `Last_Email_Date` ← set to send date
- `Email_Version` ← set to template version used
- `Email_Count` ← increment
- `Relationship_Status` ← transition from `New Prospect` to `Contacted`
- `Next_Action` ← set based on sequence position

### Output To Dashboard

All fields are available for reporting. No field is write-only.

---

## 17. Migration Note

Existing dealer JSON records in `dealer-database/outreach-ready/` use a different schema (`crm_status`, `contacts`, legacy `opportunity_scores`). When migrating:

1. Map legacy `crm_status.status` to `Relationship_Status`.
2. Map legacy `crm_status.next_action` to `Next_Action`.
3. Map legacy `best_first_product` to `Best_First_Product`.
4. Populate `Dealer_ID` from a new sequential assignment.
5. Set all reply, interest, commercial signal, and outcome fields to their default/null values.
6. Preserve existing `contacts` data in the standard `contact` object per `lead-intelligence-schema.md`.

Do not backfill historical data until the schema is approved and the migration plan is reviewed.
