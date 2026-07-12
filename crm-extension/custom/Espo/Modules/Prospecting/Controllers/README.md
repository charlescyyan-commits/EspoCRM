# Controllers — reserved for Phase 3A-2.2

No controller PHP is implemented in Phase 3A-2.1.

Future intent:

- Authenticated Prospecting Engine import controller
- Accept only `ESPOCRM_SYNC_CONTRACT_V1.json`
- Return receiver results from `ESPOCRM_SYNC_RULES_V1.md`

Must not:

- Expose a generic CRM write API
- Create Account or Opportunity records
- Call Engine scoring or research providers
