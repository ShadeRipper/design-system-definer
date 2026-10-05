# System types

A type is defined by **what varies and how independently**, not by a label. The type sets the dimensions, collections, mode names and default preset. Any combination is reachable with `custom` and `dimensions:`.

| Type | What varies | Dimensions | Preset | Generated in v1 |
| --- | --- | --- | --- | --- |
| Single brand, single theme | nothing | none | none | yes |
| Single brand, light/dark | theme | `theme` | `single-brand-light-dark` | yes |
| Multi-brand / white-label | brand | `brand` (+ `device`) | `multi-brand-white-label` | yes |
| House of brands | sub-brand inherits master, overrides a few | `brand` with inheritance | P1 | not yet |
| Multi-platform | platform conventions | `platform` | P1 | not yet |
| Responsive / multi-density | device or density | `device` | `marketing-site` (device only) | device: yes |
| Product plus marketing | expressive vs compact type and spacing | `context` | P1 | not yet |
| Accessibility variants | high contrast, reduced motion, large text | `a11y` | P1 | not yet |
| Multi-locale | script, RTL, type per locale | `locale` | P1 | not yet |
| Custom | designer picks | any | any | brand, theme, device |

## Dimension to collection

- `brand` becomes collection **Brand**, one mode per brand (plus **Base** if `base_mode: include`).
- `theme` becomes collection **Theme**, modes **Light** and **Dark** (single brand).
- `device` becomes collection **Device**, modes from `device.modes` (default Mobile, Desktop).
- No `brand` or `theme`: one collection **Brand** with a single mode named after the brand.
- Without `device`, device-level tokens (type sizes, spacing steps) live in the semantic collection at the first mode's values.

`brand` plus `theme` together is rejected in v1: it needs one mode per brand-and-theme combination. Choose one, or model dark mode as a separate system.

## Base mode (multi-brand)

Base is a neutral, unbranded mode that every brand mode compares against and components fall back to.

- `include`: white-label systems (brand unknown until runtime); components need a default look in docs and tests.
- `none`: every product ships with one of the known brands.
- `ask` (default): the interview asks once; the build refuses to run while it is still `ask`.

Base has no anchors; its primary action uses the neutral ramp. Override it with a top-level `base:` block (fonts, radius, weights).
