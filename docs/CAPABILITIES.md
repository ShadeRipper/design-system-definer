# What the Design System Definer can and can't do

Read this to know exactly what you are getting. Version 1.0.2.

**In one line:** it guides you through defining a design system, then generates accessible design tokens and the scripts that build them in Figma. It defines and builds the *foundation* (variables, modes, text styles). It does not design components or screens.

## At a glance

| Area | Status |
| --- | --- |
| Guided interview and decision brief with sign-off | Built. Run end to end, in guided mode, on a real product-and-website design. The flow is instructions for Claude, so wording varies between sessions |
| Colour ramps with guaranteed contrast | Built and tested |
| Semantic tokens (roles like text, surface, action) | Built and tested |
| Eight built-in dimensions plus custom ones | Built and tested |
| Figma variables, modes and text styles via script | Built. The generated scripts for a single brand with device, platform and context dimensions ran end to end on a real file with no errors and a checksum match. Other shapes (multi-brand, theme, density, locale) have passing tests and hand-checked mechanics but no end-to-end run yet |
| Figma native variable JSON import | Written, **not validated** against a real Figma export |
| Code tokens (DTCG, Style Dictionary) | Built and tested. A real build with Style Dictionary 5.6 produced 253 CSS custom properties with every alias resolved |
| Binding an existing design's layers to the tokens | Built (opt-in `bind` output). Run on a real 20,000-layer file: styles, colours, radius, spacing, names, verified auto-layout |
| Delta builds (only what changed) | Built |
| Audit and inventory of an existing file (read-only) | Built; run on a real file |
| Building components | Not built here; the build plan hands off to Figma's own skills |

## What it generates

From your answers, in `ds-out/`:

- **Primitives:** colour ramps (11 steps per colour), spacing, radius, border width, sizes, font sizes, line heights, weights, font families, motion durations.
- **Semantic tokens:** action colours (default, hover, pressed, border, text on it), surfaces (including inverse, deep-brand and a brand tint), text (including inverse and brand text), borders, status colours (error, success, warning, info), focus and selection indicator, radius, spacing rhythm, type, easing. Every one is an alias of a primitive; none holds a raw value.
- **Contrast matrix:** every text and UI colour pair in every mode, with its ratio, and a suggested fix for any failure.
- **Figma build scripts, text styles, build plan** with human checkpoints, **decision brief**, **decision records**, **DTCG tokens**.

## System shapes it covers

Dimensions combine freely.

| Dimension | Collection and modes | What varies |
| --- | --- | --- |
| Brand | one mode per brand, plus an optional neutral Base | colours, shape, fonts, easing |
| Theme | Light, Dark | the colour roles |
| Device | Mobile, Desktop (editable) | spacing, type sizes, margins |
| Platform | Web, iOS, Android | touch-target sizes, motion durations |
| Density | Compact, Comfortable, Spacious | padding and gaps |
| Accessibility | Default, Large text, Reduced motion | body type size, focus ring width, motion |
| Locale | Latin, Japanese, Arabic (editable) | font family per script, reading direction |
| Context | no collection | adds a marketing type scale and `Marketing/*` text styles |
| Custom | any you define | any token that aliases an existing primitive |

Also: **house of brands** (a sub-brand inherits a master and overrides a few things), **brand with light and dark** (brand palettes feed a theme layer), **one to many brands**, **Base mode on or off**, three **component-token tiers** (none, minimal, full).

## Accessibility guarantees

- Every generated colour pair is checked against **WCAG 2.x** contrast. You choose AA (text 4.5, UI 3.0), AAA (7 and 4.5) or your own ratios.
- A failing pair **blocks export** and shows a suggested fix.
- Your exact brand hex is always kept as its own token. If it can't meet the contrast target on white, the ramp is calibrated to pass and the brand colour is flagged with the text colour that works on it (for example dark text on yellow).
- Focus and selection indicators always meet the UI contrast target, even when the brand fill doesn't.

Exempt from the checks and listed in the matrix: disabled text, decorative borders, disabled and track surfaces.

**Not covered:** WCAG 3 / APCA contrast, colour-blindness simulation, and text spacing or target-size audits of finished screens.

## Where it works

| Surface | Interview and generation | Building in Figma |
| --- | --- | --- |
| Claude Code (terminal, desktop, IDE) | Yes | Yes, with the Figma connector |
| claude.ai and Claude Desktop (skill upload) | Yes | Yes, with the Figma connector |
| No Claude, command line only | Generation only (Python 3.8+) | No |

Building in Figma needs the Figma connector and edit access to a Figma Design file. It works with any such file: collections and variables are matched by name, updated if they exist and created if not, and never deleted.

## Known limits

- **Per-script line height** (for example CJK) is not generated. Add it as a custom dimension.
- **Large text** enlarges only sizes that are the same in every device mode (body text). Figma variables can't do arithmetic, so sizes that differ by device stay as they are.
- **High-contrast colour** is a contrast target (AAA), not a separate mode.
- **Platform and motion defaults** (44 and 48 point targets, durations) are common conventions. Edit them to match your guidelines.
- **Colours** are sRGB hex in, sRGB hex out. Ramps are built in OKLCH.
- **Not generated:** shadows and elevation, gradients, opacity tokens, grids, icons, illustrations.
- **Fonts:** names only. The skill never ships or installs font files; the Figma file needs the fonts, or you substitute.
- **Mode counts:** Figma limits the number of modes per collection by plan. A system with many brands may need a higher plan.
- **Existing systems:** it does not infer a system from a file; it builds from your answers. For a file that already has screens it can inventory what is used, bind layers to the new tokens and audit the result. Layers inside instances of another library's components, text that needs uppercase or underline, and large regular-weight headings (until you add regular-weight styles) are left alone and reported.

## Not in scope

Building components or screens (use Figma's `figma-generate-library` and `figma-generate-design`), choosing a brand for you, brand artwork, and coded component libraries.

## What has and hasn't been verified

| | |
| --- | --- |
| Verified by 95 automated tests | ramps, contrast across hundreds of colours at AA, AAA and custom, every dimension alone and all together, layering, ordering of collections, determinism, the sign-off gate, install packaging |
| Verified on a real file | the single-brand build (167 primitives, 27 device, 54 brand, 5 platform variables, 17 text styles) created with no errors and a checksum match; the colour, radius, spacing, naming and auto-layout binding passes on about 20,000 layers, with before and after screenshots compared pixel by pixel; a Style Dictionary 5.6 build |
| Verified by hand | the script mechanics in a real multi-brand Figma file: cross-collection aliases, modes, scopes. Output structure matches a real multi-brand Figma system |
| Not yet verified | the full generated scripts for multi-brand, theme, density and locale shapes in Figma; native JSON import; the interview across many different users and conversations |

## Versioning

Semantic versioning. From 1.0:

- **Stable within 1.x:** the config keys documented in `config-reference.md`, token and variable names, output folder and file names, exit codes, and the sign-off gate (nothing is written without `--approve`).
- **May change in a minor release:** the binding heuristics and their tolerances, preset contents, the native JSON format, and the wording of generated documents.
- A breaking change to the stable list needs a 2.0.

See [CHANGELOG.md](../CHANGELOG.md).
