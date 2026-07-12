# Multi-Product Outreach Rule

Updated: 2026-06-15

Status: Active default for all future Chitu Systems email generation tasks
unless explicitly overridden.

## Core Rule

A dealer should not receive three emails focused on the same product.

Many target dealers carry several relevant categories at once, including Bambu
A1 / A1 Mini, FDM printers, filament, Elegoo Saturn and other resin printers,
resin consumables, accessories, and spare parts.

Every outreach sequence must assign:

- `Primary_Product`
- `Secondary_Product`
- `Third_Product`

`Best_First_Product` is only the starting point for `Primary_Product`. It is not
the complete outreach sequence.

## Sequence Rotation

- Email 1 focuses on `Primary_Product`.
- Email 2 focuses on `Secondary_Product`.
- Email 3 focuses on `Third_Product`.

Each email must:

- Keep one product as the main focus.
- Introduce the product directly and use two to four real product features.
- Keep applications and customer types separate from feature bullets.
- Briefly mention other relevant opportunities only when natural.
- Avoid repeating the same product in every follow-up.
- Preserve product coverage without becoming a broad catalog pitch.

## Default Rotation

1. PlateCycler
2. Resin Tank
3. Filament Dryer

## Dealer-Specific Rotation

| Dealer profile | Primary_Product | Secondary_Product | Third_Product |
|---|---|---|---|
| Bambu-heavy | PlateCycler | Filament Dryer | Resin Tank |
| Resin-heavy | Resin Tank | PlateCycler | Filament Dryer |
| FDM / filament-heavy | Filament Dryer | PlateCycler | Resin Tank |
| Broad multi-brand | PlateCycler | Resin Tank | Filament Dryer |
| Unclear | General Partnership | PlateCycler | Resin Tank or Filament Dryer, based on available signals |

## Product Selection Controls

- Use dealer evidence, dealer tags, approved product signals, and
  `Potential_Cooperation_Products`.
- `Do_Not_Pitch` is a hard exclusion.
- Human-selected products and final human priority fields are authoritative.
- Existing partners receive relationship-expansion wording for every product
  in the rotation.
- Resin and Filament remain manual-review products unless explicitly approved.
- A product that lacks sufficient evidence should be replaced by the next
  relevant allowed product or marked for manual review.

## Universal Positioning

Every sequence should naturally communicate this idea:

> We regularly develop practical accessories and workflow-enhancement products
> for both resin and FDM 3D printing users.

Do not insert the sentence mechanically. Rephrase it when needed so the message
sounds like genuine business communication.

## Relationship To Existing Rules

- The `EMAIL_WRITING_RULES_V3.md` structure remains active.
- One main product per individual email remains active.
- Product intelligence still determines what claims may be made.
- Scoring still decides who should be contacted.
- This rule changes sequence coverage only. It does not change scoring,
  `Best_First_Product`, dealer classification, ranking, or product evidence.
