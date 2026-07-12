# Phase3B02 — CRM Workflow & Pipeline Design Report

**Date:** 2026-07-12  
**Workspace:** `D:\EspoCRM-Production`  
**Extension:** Chitu Prospecting Integration `1.2.0-alpha`  
**Scope:** CRM workflow automation, Lead pipeline design, Opportunity sales pipeline, task auto-generation, ACL verification

---

## 1. Lead Pipeline Design

### 1.1 Pipeline States

The Lead lifecycle is tracked via the `outreachStatus` field with the following states:

```
NEW ──→ RESEARCHING ──→ RESEARCH_COMPLETED ──→ QUALIFIED
                                                      │
                                                      ▼
                                              CONTACT_READY
                                                      │
                                                      ▼
                                                CONTACTED
                                                      │
                                                      ▼
                                                 RESPONDED
                                                      │
                                                      ▼
                                                 CONVERTED
                                                      │
                                                      ▼
                                                CLOSED_LOST
```

### 1.2 State Definitions

| State | Meaning | Allowed From | Responsible Role |
|-------|---------|-------------|------------------|
| **NEW** | Initial discovery; no research conducted | (initial state) | System / Research |
| **RESEARCHING** | Active research in progress | NEW | Research |
| **RESEARCH_COMPLETED** | Website analysis complete, evidence collected | RESEARCHING | Research |
| **QUALIFIED** | Lead meets qualification criteria (score, product fit) | RESEARCH_COMPLETED | System / Sales |
| **CONTACT_READY** | Contact information verified and available | RESEARCH_COMPLETED, QUALIFIED | Sales |
| **CONTACTED** | First outreach email sent | CONTACT_READY | Sales |
| **RESPONDED** | Dealer replied to outreach | CONTACTED | Sales |
| **CONVERTED** | Lead converted to Opportunity | RESPONDED | Sales / System |
| **CLOSED_LOST** | No interest, bounced, or unresponsive after sequence | Any state | Sales |

### 1.3 Field Configuration

```json
{
  "outreachStatus": {
    "type": "enum",
    "default": "NEW",
    "displayAsLabel": true,
    "options": ["NEW","RESEARCHING","RESEARCH_COMPLETED","QUALIFIED",
                "CONTACT_READY","CONTACTED","RESPONDED","CONVERTED","CLOSED_LOST"],
    "style": {
      "NEW": "default", "RESEARCHING": "warning",
      "RESEARCH_COMPLETED": "info", "QUALIFIED": "primary",
      "CONTACT_READY": "success", "CONTACTED": "primary",
      "RESPONDED": "success", "CONVERTED": "success",
      "CLOSED_LOST": "danger"
    }
  }
}
```

### 1.4 Relationship to Existing Fields

| Field | Role | Relation to Pipeline |
|-------|------|---------------------|
| `status` (native) | Sales activity status (New, Reviewed, Contacted, etc.) | Independent; tracks sales rep workflow |
| `peResearchStatus` | Research lifecycle (NONE, RESEARCHING, COMPLETED, FAILED) | Triggers pipeline automation |
| `outreachStatus` | **Pipeline master state** | Phase3B02 primary pipeline field |
| `peEmailStatus` | Email lifecycle (DRAFT_READY, APPROVED, SENT, etc.) | Parallel email tracking |
| `pePriorityLevel` | Priority (LOW, NORMAL, HIGH, URGENT) | Auto-set by scoring |

---

## 2. Automation Rules

### 2.1 Rule 1: Research Completed

**Trigger:** `peResearchStatus` changes to `COMPLETED`

**Before-Save Formula Actions:**
- `outreachStatus` → `RESEARCH_COMPLETED`

**After-Save Hook Actions:**
- Creates Task: "Prepare Outreach for {Lead Name}"
  - Priority: High
  - Due: +1 day
  - Assigned to: Lead owner

### 2.2 Rule 2: High Opportunity Lead

**Trigger:** `peOpportunityScoreV4` changes to ≥ 80

**Before-Save Formula Actions:**
- `pePriorityLevel` → `HIGH`

**After-Save Hook Actions:**
- Creates Task: "Review and Contact Lead: {Lead Name}"
  - Priority: High
  - Due: +1 day
  - Assigned to: Lead owner

### 2.3 Rule 3: Contact Ready

**Trigger:** `emailAddress` or `phoneNumber` becomes non-empty

**Before-Save Formula Actions:**
- If current `outreachStatus` is `RESEARCH_COMPLETED` or `QUALIFIED`:
  - `outreachStatus` → `CONTACT_READY`

### 2.4 Implementation Architecture

```
Lead Save
    │
    ├── Before-Save Formula (formula/Lead.json)
    │   ├── Rule 1: outreachStatus = RESEARCH_COMPLETED
    │   ├── Rule 2: pePriorityLevel = HIGH
    │   └── Rule 3: outreachStatus = CONTACT_READY
    │
    └── After-Save Hook (LeadWorkflowHook.php)
        ├── Rule 1: Create "Prepare Outreach" task
        └── Rule 2: Create "Review and Contact Lead" task
```

### 2.5 Runtime Verification

```
Created: outreachStatus=NEW | priority=NORMAL | score=50
After score 85: outreachStatus=NEW | priority=HIGH | score=85        ← Rule 2 ✓
After research COMPLETED: outreachStatus=RESEARCH_COMPLETED           ← Rule 1 ✓
After email added: outreachStatus=CONTACT_READY                       ← Rule 3 ✓
Tasks created: 2
  Task: Review and Contact Lead: ... | priority=High                  ← Rule 2 ✓
  Task: Prepare Outreach for ... | priority=High                     ← Rule 1 ✓
```

---

## 3. Task Workflow

### 3.1 Auto-Generated Tasks

| Trigger | Task Subject | Priority | Due Date | Assignee |
|---------|-------------|----------|----------|----------|
| Research Completed | "Prepare Outreach for {Lead}" | High | +1 day | Lead owner |
| Score ≥ 80 | "Review and Contact Lead: {Lead}" | High | +1 day | Lead owner |

### 3.2 Task Fields

| Field | Value | Source |
|-------|-------|--------|
| `name` | Generated subject | hook logic |
| `parentType` | `Lead` | fixed |
| `parentId` | Lead ID | `$entity->getId()` |
| `assignedUserId` | Lead owner | `$entity->get('assignedUserId')` |
| `dateStart` | Today + 1 day | `date('Y-m-d', strtotime('+1 day'))` |
| `priority` | `High` | fixed |
| `status` | `Not Started` | fixed |

---

## 4. Sales Pipeline (Opportunity)

### 4.1 Pipeline Stages

```
DISCOVERY (10%) → QUALIFICATION (25%) → CONTACTED (40%) → NEGOTIATION (60%) → WON (100%)
                                                                               │
                                                                               ▼
                                                                             LOST (0%)
```

### 4.2 Stage Definitions

| Stage | Probability | Meaning |
|-------|------------|---------|
| **DISCOVERY** | 10% | Initial opportunity identification |
| **QUALIFICATION** | 25% | Dealer qualified, product fit confirmed |
| **CONTACTED** | 40% | Outreach initiated, dealer engaged |
| **NEGOTIATION** | 60% | Active discussion: pricing, terms, samples |
| **WON** | 100% | Deal closed, partnership established |
| **LOST** | 0% | Deal lost or abandoned |

### 4.3 Compatibility

The Opportunity `stage` field is configured with Chitu pipeline stages while preserving native EspoCRM behavior:
- **Standard `probabilityMap`** — drives Opportunity probability calculations
- **Native `amount`, `closeDate`** — unchanged, continue to work
- **Native conversion lifecycle** — Lead→Opportunity conversion preserved
- **Standard reporting** — pipeline reports and dashboards function normally
- **Existing native stages** are merged into the probability map by EspoCRM

### 4.4 Stage Styles

| Stage | Badge Color |
|-------|------------|
| DISCOVERY | default (gray) |
| QUALIFICATION | info (blue) |
| CONTACTED | primary (indigo) |
| NEGOTIATION | warning (amber) |
| WON | success (green) |
| LOST | danger (red) |

---

## 5. ACL Impact

### 5.1 Role Permissions (Phase3B02)

| Role | Lead | ResearchEvidence | Opportunity | Task |
|------|------|-----------------|-------------|------|
| **Admin** | Full access | Full access | Full access | Full access |
| **Sales User** | Create/Read/Edit own | Read all | Create/Read/Edit own | Create/Read/Edit own |
| **Research User** | Read all | Create/Read/Edit all | No access | No access |

### 5.2 Field-Level ACL (Sales User — Lead)

The Sales role has **read-only** access to AI-generated fields, which is the intended design:
- `peOpportunityScoreV4`, `peScoreTier`, `peBestFirstProduct` — read-only
- `peResearchStatus`, `peResearchSummary` — read-only
- `peSyncStatus`, `peCandidateId`, `peLastSyncAt` — hidden

Formula transitions for these fields trigger only when updated through the connector (system user) or Admin UI — not from Sales manual edits.

### 5.3 ACL Verification

- Sales user can create/update Leads (own records)
- Sales user can read ResearchEvidence
- Sales user can NOT edit ResearchEvidence (403 verified in B01)
- Research user can read Leads, create/edit ResearchEvidence
- Research user has NO Opportunity or Task access
- All roles provisioned via `phase3b02_provision_workflow_pipeline.php`

---

## 6. Extension Package

### 6.1 Version

```
1.1.0-alpha → 1.2.0-alpha
```

### 6.2 Package Contents (28 files)

| Category | Files | Description |
|----------|-------|-------------|
| manifest | 1 | Package manifest |
| entityDefs | 3 | Lead, Opportunity, ResearchEvidence definitions |
| layouts | 5 | Detail/list layouts |
| formula | 1 | Lead before-save formula |
| i18n | 3 | English labels |
| hooks | 1 | LeadWorkflowHook (after-save) |
| metadata | 7 | ACL, scopes, clientDefs, selectDefs, layouts |
| PHP shells | 4 | Entities, Controllers, Select filters |
| misc | 3 | README, module.json |

### 6.3 Files Changed (Phase3B02)

- `manifest.json` — version bump, description update
- `Resources/entityDefs/Lead.json` — outreachStatus update, formula
- `Resources/entityDefs/Opportunity.json` — stage pipeline configuration
- `Resources/layouts/Lead/detail.json` — Pipeline section added
- `files/.../entityDefs/Lead.json` — mirrored
- `files/.../entityDefs/Opportunity.json` — mirrored
- `files/.../layouts/Lead/detail.json` — mirrored
- `tests/test_extension_skeleton.py` — updated for B02

### 6.4 Files Added (Phase3B02)

- `Resources/metadata/formula/Lead.json` — before-save formula
- `files/.../metadata/formula/Lead.json` — deployed formula
- `files/custom/Espo/Custom/Hooks/Lead/LeadWorkflowHook.php` — after-save hook
- `deployment/provisioning/phase3b02_provision_workflow_pipeline.php` — role provisioning
- `deployment/provisioning/phase3b02_cleanup_validation_records.php` — test cleanup

---

## 7. Test Results

### 7.1 Extension Tests (27/27 PASS)

```
test_contract_field_consistency .................... ok
test_core_espocrm_untouched ........................ ok
test_lead_extension_fields ......................... ok
test_manifest_json_valid ........................... ok
test_mvp_workflow_fields ........................... ok
test_no_database_migration_artifacts ............... ok
test_only_standard_research_evidence_php_shells_exist ok
test_phase3a26_sales_activity_workflow_metadata .... ok
test_phase3a27_email_status_integration_metadata ... ok
test_phase3a28_opportunity_workflow_metadata ....... ok
test_phase3a31_opportunity_email_lifecycle_metadata  ok
test_phase3a34_lead_layout_activation_metadata ..... ok
test_phase3b01_lead_intelligence_model ............. ok
test_phase3b02_formula_metadata_file ............... ok
test_phase3b02_lead_formula_metadata ............... ok
test_phase3b02_lead_hook_exists .................... ok
test_phase3b02_opportunity_field_count ............. ok
test_phase3b02_opportunity_pipeline_stages ......... ok
test_phase3b02_outreach_status_pipeline ............ ok
test_phase3b02_pipeline_layout_section ............. ok
test_phase3b02_surface_and_module_parity ........... ok
test_placeholder_readmes_present ................... ok
test_prospecting_engine_untouched_by_extension_tree  ok
test_required_directory_structure .................. ok
test_research_evidence_entity_created .............. ok
test_research_evidence_required_fields ............. ok
test_surface_and_module_entity_defs_match .......... ok
```

### 7.2 Connector Tests (37/37 PASS)

All 37 chitu-connector tests pass — no regression.

### 7.3 Runtime Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Extension install | PASS | v1.2.0-alpha installed (ID: 6a527d109b1467fed) |
| Rebuild | PASS | `php command.php rebuild` completed |
| Cache clear | PASS | `php command.php clear-cache` completed |
| outreachStatus metadata | PASS | API returns 9-state pipeline with styles |
| Opportunity stage metadata | PASS | API returns 6-stage pipeline with probabilityMap |
| Formula metadata | PASS | `formula.Lead.beforeSaveCustomScript` loaded (524 chars) |
| Rule 1 execution | PASS | outreachStatus → RESEARCH_COMPLETED on peResearchStatus change |
| Rule 2 execution | PASS | pePriorityLevel → HIGH on score ≥ 80 |
| Rule 3 execution | PASS | outreachStatus → CONTACT_READY on contact info |
| Task creation (Rule 1) | PASS | "Prepare Outreach" task created |
| Task creation (Rule 2) | PASS | "Review and Contact Lead" task created |
| Role provisioning | PASS | Admin, Sales User, Research User roles provisioned |

### 7.4 UI Accessibility

- **Pipeline section** in Lead detail layout show​s `outreachStatus`, `pePriorityLevel`, `nextFollowUpAt`, `lastContactAt`
- outreachStatus displays as color-coded label (default/warning/info/primary/success/danger)
- Opportunity detail layout shows pipeline stage in Overview section

---

## 8. Limitations

1. **Formula-only field updates**: The before-save formula handles field transitions but cannot create Tasks. Task creation requires the after-save PHP hook (`LeadWorkflowHook.php`). This is a known EspoCRM formula limitation.

2. **No email sending**: This phase does not implement email generation or SMTP integration. The pipeline states `CONTACTED` and `RESPONDED` are set manually or via future connector sync.

3. **No BPM/Advanced Pack**: The automation uses native EspoCRM formula + hooks, not the Advanced Pack workflow engine. Complex multi-step workflows (e.g., email sequences with delays) are not implemented.

4. **Sales user field restrictions**: Sales users cannot edit `peOpportunityScoreV4` or `peResearchStatus` by ACL design. Formula Rules 1 and 2 only trigger when these fields are updated by the connector (system user) or Admin.

5. **Duplicate task prevention**: The hook creates a task every time the trigger condition is met on save. If a Lead is saved multiple times with `peResearchStatus = COMPLETED`, duplicate tasks may be created. Future phases should add deduplication logic.

6. **No reply tracking**: `RESPONDED` state requires manual update. No IMAP/email integration is configured to auto-detect replies.

7. **Local test container only**: Runtime verification was performed on the disposable local EspoCRM-Test container. Production deployment requires separate provisioning.

8. **Opportunity stage merge**: The custom Chitu pipeline stages (DISCOVERY, etc.) are merged with native EspoCRM stages (Prospecting, Qualification, etc.) in the probability map. Both sets appear in the stage dropdown. A future cleanup phase should standardize on one set.

---

## 9. Deployment Artifacts

| Artifact | Path |
|----------|------|
| Extension package | `deployment/prospecting-extension-v1.2.0-alpha.zip` |
| Provisioning script | `deployment/provisioning/phase3b02_provision_workflow_pipeline.php` |
| Cleanup script | `deployment/provisioning/phase3b02_cleanup_validation_records.php` |
| Extension source | `crm-extension/` |
| Test suite | `crm-extension/tests/test_extension_skeleton.py` (27 tests) |

---

**Phase3B02 completed. Stop here and await the next phase instruction.**
