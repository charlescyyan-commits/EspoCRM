# LCD Outreach Intelligence V1

Updated: 2026-06-09

Purpose: Replace generic LCD category outreach with model-specific replacement-screen outreach.

## Core Rule

Do not sell an abstract LCD category.

Sell the supported LCD models that match the dealer's existing resin-printer brands.

Every LCD email must name at least one supported printer family. If no supported brand evidence exists, do not generate the LCD email automatically. Set it aside for manual review.

## Product Positioning

### Do Not Use

> Replacement LCD supply gives dealers a practical maintenance category.

This leaves the dealer's first question unanswered: which printer models are supported?

### Use

> We currently supply replacement LCD screens for the following printer families...

Then name only the families supported by dealer evidence.

## Supported Model Library

### ELEGOO

Primary models:

- Saturn 4 Ultra
- Saturn 4
- Saturn 3 Ultra
- Saturn 3
- Mars 5 Ultra
- Mars 5
- Mars 4 Ultra
- Mars 4
- Jupiter

Email family language:

- Saturn Series
- Mars Series
- Jupiter

Compact supported-model wording:

`Saturn Series (Saturn 3, Saturn 3 Ultra, Saturn 4, and Saturn 4 Ultra), Mars Series (Mars 4, Mars 4 Ultra, Mars 5, and Mars 5 Ultra), and Jupiter.`

### ANYCUBIC

Primary models:

- Photon Mono M7 Pro
- Photon Mono M7
- Photon Mono M5s
- Photon Mono M5
- Photon Mono X
- Photon Mono X2

Email family language:

- Photon Mono Series

Compact supported-model wording:

`Photon Mono Series, including M5, M5s, M7, M7 Pro, Mono X, and Mono X2.`

### CREALITY

Primary models:

- HALOT Series

Email family language:

- HALOT Series

### PHROZEN

Primary models:

- Sonic Series

Email family language:

- Sonic Series

## Dealer Matching

Use the dealer profile's commercial evidence:

| Dealer evidence | LCD family to mention |
| --- | --- |
| `sells_elegoo = true` | Saturn Series, Mars Series, Jupiter |
| `sells_anycubic = true` | Photon Mono Series |
| `sells_creality = true` | HALOT Series |
| `sells_phrozen = true` | Sonic Series |

If multiple supported brands are present, include every matched family. Do not choose one brand arbitrarily.

Do not infer brand support from a generic resin-printer flag.

## Required Email Structure

### 1. Observation

Use verified dealer evidence.

Example:

`I noticed you carry Elegoo resin printers alongside FEP and other maintenance parts.`

### 2. Customer Problem

`Many resin printer owners eventually require an LCD replacement after long-term use or screen failure.`

### 3. Product Introduction

`We currently supply replacement LCD screens for:`

Then list the dealer-matched supported families and models.

### 4. Advantages

1. Compatible replacement screens for popular resin printers
2. Fits naturally alongside FEP, VAT, resin tank, and ACF consumables
3. Supports repair and maintenance customers
4. Creates ongoing aftermarket sales opportunities

### 5. Question

`Would this LCD range be relevant for your customers?`

The question may be rotated, but it must remain a simple relevance question and must not ask for a meeting.

## Maintenance Emphasis

Increase repair, maintenance, downtime, and aftermarket emphasis when the dealer already sells any of:

- FEP
- VAT
- Resin tanks
- ACF
- Replacement LCDs

This emphasis supplements model specificity. It never replaces the supported-model list.

## Existing Partners

Existing partners receive relationship-expansion wording.

The email should acknowledge current cooperation, then introduce the supported LCD families as a complementary product opportunity.

## Forbidden Messaging

Do not write these phrases without naming supported models in the same email:

- LCD market
- LCD category
- LCD business
- aftermarket demand

Avoid generic statements such as:

- replacement LCD supply
- resin-printer repair opportunity
- practical maintenance category

unless the email immediately identifies the supported printer families.

## Generation Gate

An automatically generated LCD email must pass all checks:

1. Dealer evidence includes ELEGOO, ANYCUBIC, CREALITY, or PHROZEN.
2. The email names every matched supported family.
3. The customer problem is present.
4. The product introduction says replacement LCD screens.
5. Generic LCD-market language does not appear without supported models.
6. FEP/VAT/resin-tank/ACF evidence activates stronger maintenance language.

If any check fails:

`Manual_Review_Required = Yes`

No confident LCD sequence should be generated.
