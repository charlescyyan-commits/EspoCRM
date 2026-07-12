# Resources design surface

Top-level `Resources/` mirrors the EspoCRM metadata categories required by Phase 3A-2.1:

- `entityDefs/` — ResearchEvidence + Lead overlay
- `layouts/` — ResearchEvidence detail/list
- `acl/` — ResearchEvidence ACL stub
- `metadata/` — reserved for future app-level metadata

The installable copies used by EspoCRM packaging live under:

`files/custom/Espo/Modules/Prospecting/Resources/`

Keep both trees aligned. Skeleton tests verify entityDefs parity.
