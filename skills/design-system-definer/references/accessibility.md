# Accessibility rules

Contrast uses WCAG 2.x relative luminance. Targets come from `color.contrast`: `AA` (text 4.5, UI 3.0), `AAA` (7.0, 4.5) or custom `{text, ui}` (`ui` may not exceed `text`).

## Ramps (R3)

Against white, step **500** meets the UI target and step **600** meets the text target; every step above 600 meets the text target. Ramps are built in OKLCH from each anchor's hue and chroma, with chroma clamped to sRGB.

**Contrast wins over anchor fidelity.** The exact anchor hex is kept as the ramp step nearest to it by lightness, but only if that step's requirement still holds. Otherwise the ramp is calibrated and the anchor is flagged with the text color that works on it (usually black on a light brand color like yellow). The decision brief states which case applies per anchor.

## Indicator versus action split

A brand fill can be a good *button* and a bad *focus ring*. A light fill (yellow on white is about 1.5:1) fails the 3:1 non-text requirement for focus and selection indicators.

- `color/action/primary/default`: the fill. Text on it (`color/action/on-primary`) must meet the text target; the skill chooses white or the darkest neutral, whichever passes. If neither passes, the fill moves to a step where one does.
- `color/action/primary/border`: carries the 3:1 edge when the fill alone does not meet it against the page.
- `color/indicator`: the first ramp step at or beyond the fill (and at least 500) that meets the UI target on both page and card. Use it for focus rings, checked marks, selected borders, progress fills. `color/on-indicator` is the mark drawn on it.

## Pairs checked in every mode

Text: primary and secondary on page and card; on-primary on default, hover and pressed fills; on-brand on brand surface; on-indicator on indicator; each status text on card and on its own surface.
UI: indicator and default border on page and card; primary border on page; each status border on card.

Exempt, and listed in the matrix notes: disabled text, subtle (decorative) borders, disabled and track surfaces.

A failing pair blocks export and prints a suggested fix (a nudged foreground that passes). When no foreground can pass (the background is the problem) the fix column is empty and the message says to change the background.

## Dark mode

Same roles, mirrored: page and card use dark neutral steps; text, borders and status colors search toward lighter steps; the action fill is lightened until it meets the UI target against the dark page; on-primary prefers the darkest neutral. Hover and pressed steps only go where the text on the fill still passes.

## Targets and other defaults

Minimum touch target 44 (48 default `size/control`). Focus ring width 2 (3 for the roomiest brands via `border.focus`). Reduced motion and high-contrast variants are P1 dimensions.
