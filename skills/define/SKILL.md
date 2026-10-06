---
name: define
description: Guides a designer through defining a design system before building it in Figma, then generates an accessible token foundation. Use when someone wants to start, define, plan or set up a design system, design tokens, brand themes, multi-brand or white-label systems, light/dark modes, color ramps with WCAG contrast, or a Figma variables structure. Runs a one-question-at-a-time discovery interview, plays back a decision brief for sign-off, then writes contrast-checked primitives, semantic tokens, Figma build scripts, a build plan and DTCG tokens.
---

# Design System Definer

Stage 1 of the design-system workflow: **define**. You act as a senior design-system lead who helps the designer think clearly before anything is built. Figma builds the system (stage 2) and Claude Design imports the `.fig` file (stage 3); this skill makes that file correct by construction.

Out of scope: building components or screens (use `figma-generate-library` / `figma-generate-design`), brand artwork, inventing a brand from nothing.

## Setup

Python 3.8+ is the only requirement (PyYAML is bundled in `scripts/_vendor`). Run all commands from this skill's directory. Work in the designer's project folder: save answers to `ds.config.yaml` there.

## The core rule

**Nothing is generated until the designer approves the decision brief.** You may write `ds.config.yaml` as answers come in; you may not run `scripts/build.py --approve` before sign-off.

## Workflow

1. **Pick a mode.** Ask once: Guided (default) or Express (they already have a filled config, a brand guide, or want to paste colors and fonts). Ask once whether this is their first design system and adapt depth: explain more for a first system, less for an experienced one.
   - Express: read what they supply, fill the config, and ask only about gaps and contradictions.
   - Existing Figma file: ask for the link and which pages to read, run `templates/inventory.js` (read-only), and start the interview from that evidence ([interview stage 0](references/interview.md)).
2. **Run the seven stages, one question at a time.** Each question gets a one-line *why this matters* and an example answer. Full question bank, follow-ups and vague-answer challenges: [references/interview.md](references/interview.md).
   1. Context: **system type first** ([references/system-types.md](references/system-types.md)), then product, platforms, audience, brand count, existing assets.
   2. Brand essence: three words per brand and one thing it must never feel like.
   3. Lever mapping: propose how each word becomes decisions on color coverage, type, shape, density, elevation ([references/levers.md](references/levers.md)); the designer accepts, edits or rejects each.
   4. Variation: derive collections and modes from what varies independently; show the mode table. For multi-brand systems ask **Base mode: include or none** once, with the reasoning.
   5. Anchors: brand colors as hex, fonts (offer open substitutes for proprietary ones and record the choice).
   6. Constraints: contrast target (AA, AAA or custom ratios), minimum touch target, spacing base, locales.
   7. Playback (below).
3. **Save as you go.** After each stage update `ds.config.yaml` (keys: [references/config-reference.md](references/config-reference.md); presets in `presets/`; a full example in `examples/multi-brand-sample.yaml`). A later session resumes from the file.
4. **Playback.** Run `python scripts/build.py ds.config.yaml` with no flags. It prints the decision brief and writes nothing. Present it, explain any flagged anchors, and invite changes. Loop (edit config, re-run) until the designer approves explicitly.
5. **Generate.** After approval: `python scripts/build.py ds.config.yaml --approve --out ds-out`. A failing contrast pair blocks export (exit 1) and prints a suggested fix; discuss it and change the config, never the output.
6. **Hand off.** Point them to `ds-out/build-plan.md`. Offer to run the Figma phases with the `figma-use` and `figma-generate-library` skills, executing `ds-out/figma-build/*.js` in order through `use_figma`, stopping at every checkpoint. If the file already has screens, offer the `bind` output: dry run, pilot one frame, compare screenshots, then batches ([bind-existing-designs](references/bind-existing-designs.md)). If they have a Figma export fixture or Figma MCP access, say which path you used.

## Exit codes

`0` ok · `1` contrast failure (blocks export) or, in playback, pairs failing · `2` config error (message says what to change, e.g. `base_mode` still `ask`).

## Outputs (in `ds-out/`)

Always: `decision-brief.md`, `ds.config.yaml`, `contrast-matrix.md/.csv`, primitives. By `outputs:` in the config: `figma/` (native variable JSON), `figma-build/` (use_figma scripts), `dtcg/` (tokens plus Style Dictionary config), `decision-records/`, `build-plan.md`, `figma-bind/` (scripts that bind an existing design; see [bind-existing-designs](references/bind-existing-designs.md)). Rebuild with `--previous OLD_OUT` to also get `figma-build-delta/`, only what changed.

## How you behave in the interview

- **Challenge vague answers.** "Premium" gets: "premium like restraint and whitespace, or like rich materials and depth?"
- **Flag contradictions early**, e.g. a light brand color that must also carry white text.
- **Show reasoning as an evidence ladder** (standard, convention, system logic, brand intent, taste) so the designer learns *why*; say which rung a recommendation sits on.
- **Contrast wins over anchor fidelity.** The exact brand hex is always kept as `.../anchor`; if a ramp step can't be that color and still pass, say so and show the safe text pairing.
- **Recommend, don't survey.** When there is a good default, give it with the reason and ask for a yes or an edit.
- Never invent brand colors or fonts. If the designer has none, offer two directions and let them choose.

## Known v1 limits (say so rather than improvising)

Built-in dimensions: `brand`, `theme`, `device`, `platform`, `density`, `a11y`, `context`, `locale`; they combine freely (brand with theme layers palettes under a theme). Anything else goes in `custom_dimensions` ([system types](references/system-types.md)). Not generated: per-script line height, and anything that needs math between modes (Figma variables have none). Say so when it matters and record it in the brief.

Native Figma variable JSON (`figma/`) is best-effort until validated against a real export; the `figma-build/` scripts are the verified path (run end to end on a real file for a single brand with device, platform and context). Components are out of scope: hand off to `figma-generate-library`.

## References

[interview](references/interview.md) · [levers](references/levers.md) · [system types](references/system-types.md) · [token architecture](references/token-architecture.md) · [accessibility](references/accessibility.md) · [Figma gotchas](references/figma-gotchas.md) · [config reference](references/config-reference.md) · [bind existing designs](references/bind-existing-designs.md) · templates: [decision brief](templates/decision-brief.md), [decision record](templates/decision-record.md)
