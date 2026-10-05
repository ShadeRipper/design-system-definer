# PRD — Design System Definer Skill

Oct 5, 2026 · @Gaurav Sharma

## Summary and problem

The Design System Definer is a Claude skill that turns a designer's brand thinking into an accessible, build-ready token foundation and a Figma build plan. It covers only stage 1 of the workflow; Figma builds the system and Claude Design imports it from the `.fig` file.

**Problem.** Designers usually open Figma with fuzzy intent. Colors get picked by eye, contrast is checked late, and modes are bolted on after components exist. The result is rework that shows up exactly when the system is supposed to be done.

**Evidence from the Multi-Brand DS build (Cars24 task, Oct 2026).** Most rework traced back to stage-1 decisions made too late:

- Brands created as separate collections instead of modes, then rebuilt.
- Lay's yellow failed contrast with white text and as a focus/selection indicator, which forced two new tokens mid-build.
- Components bound to primitives, variables nested in the wrong groups, and names with spaces or brackets, all fixed by hand.
- Missing tokens (control height, round radius, track color) discovered only while building components.

Each of these is a decision the skill can force before the first Figma layer exists.

## Goals and non-goals

**Goals**

1. A designer goes from blank page to a signed-off token foundation in under 45 minutes for a system of 1 to 4 brands.
2. Every text and UI color pair passes WCAG AA in every mode by construction, before anything reaches Figma.
3. Zero restructuring of collections or modes after the Figma build starts.
4. Outputs import into Figma without errors and hand off cleanly to Figma's official `figma-generate-library` skill.
5. The designer can explain every token decision afterwards, in a review or an interview.

**Non-goals**

| Out of scope | Why |
| --- | --- |
| Building components or screens in Figma | `figma-generate-library` and `figma-generate-design` already do this well |
| Converting the system for Claude Design | Claude Design imports the `.fig` file directly; the skill only makes sure the file is import-ready |
| Brand artwork and illustration | A brand asset, not part of the system; needs art direction each time |
| Coded component libraries | The skill exports tokens for code; components belong to the codebase |
| Choosing the brand itself | The skill sharpens brand intent; it does not invent a brand from nothing |

## Users and user stories

Three users share one need: decisions made deliberately, before building.

| User | Starting point | What they need most |
| --- | --- | --- |
| Product designer starting a new system | A brand idea, maybe a logo and two colors | Guidance to turn vague intent into concrete decisions |
| Design system designer (multi-brand or white-label) | Several brands or themes on one core | Correct collection and mode structure, contrast per brand |
| Design engineer | Tokens needed in code too | The same decisions exported as code-ready tokens |

**Stories, in priority order**

- As a product designer, I want to be asked the right questions one at a time, so that I discover what my brand actually means visually before I pick a single color.
- As a product designer, I want vague words like "premium" or "energetic" translated into concrete levers (color coverage, type, shape, density), so that my choices are defensible.
- As a design system designer, I want the skill to work out how many collections and modes I need from the ways my system varies, so that I never rebuild the structure later.
- As a design system designer, I want every brand's colors checked for contrast before export, with a suggested fix when one fails, so that accessibility problems never reach Figma.
- As any user, I want to review a one-page decision brief and approve it before any file is generated, so that I stay in control.
- As any user, I want to change one setting in a config file and regenerate, so that I can explore options without redoing the interview.
- As a design engineer, I want the same tokens as DTCG JSON, so that code and Figma share one source of truth.
- Edge case: as a user with an existing brand guide, I want to paste my colors and fonts and skip questions I have already answered.

## Where the skill sits in the workflow

The skill owns step 1 and prepares the hand-offs; every later step uses existing tools.

1. **Define (this skill).** Discovery interview, decision brief, sign-off, then token files and a build plan.
2. **Build in Figma.** Import the variable JSON with Figma's native Import, then run `figma-generate-library` with the build plan for styles and components.
3. **Hand off to Claude Design.** Download the `.fig` file and import it into Claude Design.
4. **Code (optional).** Use the DTCG export with Style Dictionary to produce CSS variables per brand or theme.

**What this means for the outputs.** Claude Design learns the system from what is inside the `.fig` file. So the skill's job is to make that file self-explanatory: variables organised in modes, text styles bound to variables, a description on every semantic token, and consistent names. A clean file is the bridge.

## System types

A design system type is defined by **what varies and how independently**, not by a label. The interview's first question picks a type; the type sets the dimensions, collections, mode names and default preset. Any combination is allowed, so a type that is not listed is still reachable by choosing "custom" and picking dimensions directly.

| Type | What varies | Dimensions (collections) | Base mode default |
| --- | --- | --- | --- |
| Single brand, single theme | Nothing | none (primitives + semantic) | n/a |
| Single brand, light/dark | Theme | theme | n/a |
| Multi-brand / white-label | Brand, optionally theme | brand (+ theme) | **ask** (see below) |
| House of brands (master brand plus sub-brands) | Sub-brand inherits master tokens, overrides a few | brand, with inheritance | none |
| Multi-platform (web, iOS, Android) | Platform conventions | platform (+ theme) | n/a |
| Responsive / multi-density | Device or density | device or density | n/a |
| Product and marketing hybrid | Expressive vs. compact type and spacing | context (product, marketing) | n/a |
| Accessibility variants | High contrast, reduced motion, large text | a11y (+ theme) | n/a |
| Multi-locale | Script, RTL, type scale per locale | locale | n/a |
| Custom | Designer picks the dimensions | any | ask |

**Base mode (multi-brand).** Base is a neutral, unbranded mode that every brand mode can be compared against and that components fall back to.

- `base_mode: include` adds it. Choose this for white-label systems, where the brand is unknown until runtime, and when components need a default look in documentation and tests.
- `base_mode: none` omits it. Choose this when every product always ships with one of the known brands.
- `base_mode: ask` (default) makes the interview ask once, with that reasoning shown.
- When included, Base gets the same contrast checks as any brand.

Choosing a type also changes the interview: stage 4 (Variation) is pre-filled from the type and the designer edits it, rather than building it from nothing.

## The discovery interview

The interview is the skill's personal touch: it acts like a senior design-system lead who helps the designer think clearly, one question at a time, before anything is generated.

**Two modes**

- **Guided** (default): one question at a time, each with a one-line "why this matters" and an example answer.
- **Express**: the designer pastes or points to a filled config; the skill asks only about gaps and contradictions.

**The seven stages**

1. **Context.** System type first (see System types), then product, platforms, audience, number of brands, existing assets (logo, colors, fonts, a brand guide).
2. **Brand essence.** Three words per brand, plus one thing it must never feel like.
3. **Lever mapping.** The skill proposes how each word becomes decisions on five levers (color coverage, type character, shape, density, elevation) and explains why. The designer accepts, edits or rejects each one.
4. **Variation.** Which dimensions vary independently: brand, light/dark, density, device, platform. The skill derives one collection per dimension and shows the mode table.
5. **Anchors.** Brand colors as hex, fonts (licensed, or open substitutes the skill suggests).
6. **Constraints.** Contrast target (AA or AAA), minimum touch target, spacing base unit, locales.
7. **Playback.** A one-page decision brief listing every decision with its reason. Nothing is generated until the designer approves it.

**How it stays personal**

- Adapts depth to experience: it asks once whether this is the designer's first system and explains more or less accordingly.
- Challenges vague answers. "Premium" prompts a follow-up such as "premium like restraint and whitespace, or like rich materials and depth?"
- Flags contradictions early, for example a light brand color that is also meant to carry white text.
- Shows its reasoning as an evidence ladder (standard, convention, system logic, brand intent, taste), so the designer learns why, not only what.
- Saves answers to the config, so the next session starts where the last one stopped.

## Outputs

After sign-off the skill writes eight files; the first four are required for every run.

| Output | Format | Used by |
| --- | --- | --- |
| Decision brief | Markdown | The designer, stakeholders, reviewers |
| `ds.config.yaml` | YAML | Reruns and customization |
| Primitives (contrast-calibrated ramps, spacing, radius, type scale) | JSON in Figma's native variable format | Figma Import |
| Contrast matrix, every pair in every mode | Markdown + CSV | QA and the system's documentation |
| Semantic and device tokens with aliases | JSON, plus a fallback Figma build script | Figma (Import or script) |
| Figma build plan: phases, order, checkpoints | Markdown checklist | `figma-generate-library` |
| Decision records, one per key decision | Markdown | Reviews and interviews |
| DTCG token export | JSON | Style Dictionary and code |

Figma's native import uses color objects (color space, components, alpha, hex), not plain hex strings; plain hex is silently skipped. The skill must write that exact format.

## Customization

Every rule in the skill is a default that a config can override, so one skill fits any new system.

**Override order** (later wins): skill defaults, then a preset, then the project config, then per-brand overrides.

**Presets shipped with v1**

- `single-brand-light-dark`: one brand, light and dark themes.
- `multi-brand-white-label`: several brands on one brand-agnostic core, plus a neutral Base mode.
- `marketing-site`: one brand, expressive type scale, device modes only.

P1 presets follow the remaining system types: `house-of-brands`, `multi-platform`, `responsive-density`, `product-marketing`, `accessibility-variants`, `multi-locale`. A designer can always choose `custom` in v1.

**Example config**

```yaml
preset: multi-brand-white-label
system_type: multi-brand            # see System types; custom allowed
base_mode: ask                      # include | none | ask (multi-brand only)
dimensions: [brand, device]        # add theme for light/dark
brands:
  - name: Lay's
    essence: [cheerful, playful, snackable]
    never: corporate
    anchors: { primary: "#FFC72C", accent: "#D52B1E" }
    fonts: { heading: Nunito, body: Nunito }
    overrides: { radius.control: 4 }
color:
  space: oklch
  steps: [50,100,200,300,400,500,600,700,800,900,950]
  contrast: { text: 4.5, ui: 3.0 }   # AA default. AAA: { text: 7, ui: 4.5 }. Any custom values allowed
spacing: { base: 4 }
type: { scale: [12,14,16,18,20,24,28,32,40,48], desktop_headings_scale: true }
naming: { color: element-first, type: property-first, primitives_prefix: font, semantic_prefix: type }
tiers: { component_tokens: minimal }  # none | minimal | full
components: [button, text-field, checkbox, radio, selectable-card, progress, feedback]
outputs: [figma, dtcg, decision-records]
```

**What a designer can change without touching the skill:** dimensions and modes, ramp steps and contrast targets, the spacing base, the type scale, naming conventions, how many component-level tokens to create, the component list handed to the build plan, and which outputs to generate.

## Requirements

Nine P0 requirements make v1; each has a test Claude Code can run.

**P0: must ship**

| ID | Requirement | Acceptance criteria |
| --- | --- | --- |
| R1 | Guided interview with playback and sign-off | No file is written before the designer approves the decision brief; the brief lists every decision with a reason |
| R2 | Collections derived from variation dimensions | One collection per independent dimension; mode names shown and confirmed; brands are never separate collections |
| R3 | Contrast-calibrated ramps in OKLCH from anchor colors, with a selectable contrast target | Targets come from `color.contrast` (AA 4.5 / 3.0 by default, AAA 7 / 4.5, or custom values). For every ramp, step 500 meets the UI target and step 600 meets the text target against white. **Contrast wins over anchor fidelity:** the exact anchor hex is always kept as its own `brand/anchor` primitive; it lands on its nearest ramp step only if that step passes, otherwise the ramp is calibrated and the skill flags the anchor with a safe pairing (for example dark text on Lay's yellow) |
| R4 | Semantic tokens generated per mode, aliases only | Zero raw color or number values in the semantic tier (strings and booleans excepted); names follow the config |
| R5 | Contrast matrix per mode | Every text, border and indicator pair listed with its ratio; a failing pair blocks export and comes with a suggested fix |
| R6 | Figma-importable JSON | Imports into Figma with no errors and no skipped variables; validated against a real Figma export fixture |
| R7 | Build plan for `figma-generate-library` | Ordered phases with a human checkpoint after foundations and after each component |
| R8 | Config save and rerun | Editing one value and rerunning regenerates the outputs deterministically |
| R9 | System type selection | The interview asks the type first; the type pre-fills dimensions and mode names; `custom` accepts any dimensions; in multi-brand systems `base_mode` include, none or ask is honored and Base, when included, passes the same contrast checks |

**P1: fast follow**

- Express mode driven entirely by a filled config.
- Decision records generated from the brief.
- DTCG export plus a Style Dictionary config.
- A Figma gotchas checklist built into the build plan (see the constraints section).
- Light/dark as a theme dimension in every preset.
- A library of essence-to-lever suggestions (for example "premium" mapped to restraint, whitespace and lighter weights).

**P2: later**

- A live configurator artifact for editing the config visually.
- A Figma plugin version that runs without Claude.
- Audit mode on an existing file, reusing the `design:design-system` skill.
- iOS and Android token outputs.

## Skill architecture

A lean `SKILL.md` runs the interview and routes to references and scripts only when a stage needs them.

```
ds-definer/
├─ SKILL.md                    workflow, interview stages, sign-off rule, routing
├─ references/
│   ├─ interview.md            questions, why-lines, follow-ups for vague answers
│   ├─ levers.md               essence-to-lever library, evidence ladder
│   ├─ system-types.md         type catalog, dimensions per type, base-mode guidance
│   ├─ token-architecture.md   tiers, deriving collections, naming conventions
│   ├─ accessibility.md        contrast rules, indicator vs action split, targets
│   └─ figma-gotchas.md        known Figma API and import pitfalls
├─ presets/
│   ├─ single-brand-light-dark.yaml
│   ├─ multi-brand-white-label.yaml
│   └─ marketing-site.yaml
├─ scripts/
│   ├─ ramps.py                OKLCH ramps calibrated to target contrast
│   ├─ semantic.py             semantic and device tokens per mode
│   ├─ contrast.py             contrast matrix and suggested fixes
│   ├─ export_figma.py         Figma native variable JSON
│   ├─ export_dtcg.py          DTCG JSON and Style Dictionary config
│   └─ build_plan.py           phased plan for figma-generate-library
├─ templates/
│   ├─ decision-brief.md
│   └─ decision-record.md
└─ tests/
    ├─ fixtures/figma-export-sample.json
    └─ cases/                  briefs from this project as regression tests
```

**Notes for Claude Code**

- Scripts are deterministic and take only the config as input, which keeps R8 testable.
- The Lay's, Pepsi, Starbucks and Base set from this project becomes the first regression case; Lay's yellow is the stress test for contrast.
- The skill calls other skills by name rather than copying them: `figma-generate-library` and `figma-use` for the build, and optionally the community `design-tokens` skill for DTCG validation.

## Success metrics, constraints and open questions

**Success metrics**

| Metric | Target | Type |
| --- | --- | --- |
| Time from first question to signed-off brief and token foundation | Under 45 minutes (matches Goal 1) | Leading |
| Contrast pairs failing at export | 0 | Leading |
| Figma import errors or skipped variables | 0 | Leading |
| Collection or mode restructures after the Figma build starts | 0 | Lagging |
| Decisions the designer can explain in a review without notes | All key decisions | Lagging |

**Constraints and known Figma gotchas** (these go into `figma-gotchas.md`)

- Plain-hex colors are skipped on import; use Figma's color-object format.
- Opacity set on a variable-bound paint can reset to 100%; use layer opacity for translucency.
- Shadow spread renders only with Clip content on; focus rings depend on it.
- A text component property shares one default value across all variants.
- Brand tokens can alias Device tokens across collections, and both modes resolve.
- Names with spaces or brackets break code export; enforce lowercase slash paths.
- Figma MCP calls are rate-limited by plan, so the build plan runs in phases.
- Brand fonts are often proprietary; the interview offers open substitutes and records the choice.

**Open questions**

- [x] Claude Design and the `.fig` file: assumed to carry modes, descriptions and text-style bindings. **Fallback if not:** read the variables directly from the Figma file through the Figma MCP, write them to an export folder, and add that folder to Claude Design. Verify once with this project's file; it no longer blocks R6.
- [ ] Does Figma's native JSON import keep cross-collection aliases? If not, semantic tokens go in through the fallback build script. (Owner: Claude Code, in phase 1)
- [x] Component-level tokens default to `minimal` (decided). Missing control-height, radius and track tokens were a main cause of rework.
- [x] Base mode is a per-system choice (`base_mode: include | none | ask`), driven by system type; see System types.

**Build plan for Claude Code**

1. Scripts and tests: ramps, contrast, Figma and DTCG export, validated against the fixture and this project's brands.
2. `SKILL.md` and the interview references, with sign-off gating.
3. Presets, config overrides and the build-plan generator.
4. Evaluation: run three test briefs (single brand, multi-brand, light/dark) end to end, then import into Figma and into Claude Design.
