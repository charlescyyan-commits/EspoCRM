# Diagrams Index

**Status:** Static Verified — diagrams reference implemented or contract-defined flows only

## In-Repository Diagrams

| Diagram | Location | Description |
|---------|----------|-------------|
| System acquisition vs sync | [architecture/SYSTEM_OVERVIEW.md](../architecture/SYSTEM_OVERVIEW.md) | SearchStrategy/Job/Pool vs Lead sync |
| Chitu sync sequence | [architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md) | Connector → `/Prospecting/sync/*` |
| Feedback loop | [architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md) | SalesFeedback → LearningSignal |
| Brevo email events | [architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md) | EmailEvent ingestion |
| SearchStrategy → SearchJob | [architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md) | generate-jobs API |
| Worker lifecycle | [architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md) | claim → provider → ProspectPool |
| Release process | [release/RELEASE_PROCESS.md](../release/RELEASE_PROCESS.md) | Build and verify flow |

## Historical / Audit Diagrams

| Diagram | Location |
|---------|----------|
| Acquisition architecture map | [PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md](../PHASE3C02_2A_ACQUISITION_RUNTIME_BOUNDARY_AUDIT.md) |
| Phase 3B architecture | [ARCHITECTURE_PHASE3B.md](../ARCHITECTURE_PHASE3B.md) |

**Note:** The 2A audit predates C02.2C runner implementation; see [DATA_FLOW.md](../architecture/DATA_FLOW.md) for current adapter status.

## Suggested Future Diagrams (Not Drawn)

Insufficient single-source evidence to render without speculation:

- Multi-runner concurrent claim race (design discussion only)
- Live Google/Apify provider flow (**Not Implemented**)
- ProspectPool → Lead automatic push (**Not Implemented**)

## Mermaid Guidelines

- Keep diagrams small and renderable in standard Markdown viewers
- Label edges with **Implemented** vs **Not Implemented** where mixed
- Do not depict automatic Opportunity creation

## Related Documents

- [../architecture/DATA_FLOW.md](../architecture/DATA_FLOW.md)
- [../architecture/BOUNDARIES.md](../architecture/BOUNDARIES.md)
