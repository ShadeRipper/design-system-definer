# Changelog

Versions follow [semantic versioning](https://semver.org). Below 1.0, a minor bump (0.x) adds capability and may change details; a patch bump (0.x.y) is fixes only.

## 0.8.0

- **Audit** (`figma-bind/03-audit.js`): a read-only coverage report of an existing file: text styled, colours, radius and spacing bound, auto-layout share, generic names, and the top unbound values. Run it before to see the gap and after to prove the result.
- **Inventory** (`templates/inventory.js`): read-only, needs no config. Tallies the fonts, sizes, colours by area, radii and spacing a file really uses, so the interview starts from evidence.
- **Interview stage 0 for an existing file**: ask for the link and which pages to read, run the inventory, present what the evidence says before asking, and say up front what the system will not cover (chart colours, illustration).
- Font question now asks whether a family is used for a specific job (navigation, buttons, labels), which is what `fonts.ui` is for.
- New preset `web-product-and-site`: a web product plus a marketing site on one brand, desktop and web only, with room to add mobile and other platforms.
- 95 tests (from 92).

## 0.6.0

- **Bind an existing design.** With `outputs: [..., bind]` the build writes `figma-bind/`: scripts, generated from your config, that bind a file's existing layers to the tokens. Text styles (by family role, weight and size), colour variables (nearest in Lab, semantic preferred, text colour by background), radius, spacing, role names and verified auto-layout. Dry run by default; every auto-layout change is checked and rolled back if a child moves.
- **Delta builds.** `build.py ... --previous OLD_OUT` writes `figma-build-delta/`: only new or changed variables and text styles, plus a list of what was removed (never deleted for you).
- New reference: `bind-existing-designs.md` with the method, the rules and eight gotchas found on a real file.
- The build plan gains a "bind the existing screens" phase when `bind` is on.
- 92 tests (from 83); generated scripts are syntax-checked with Node when it is installed.

## 0.4.0

- Tested on a real product-and-website file: the first end-to-end run of the interview, build and Figma scripts on an existing design.

- New colour roles: `surface/inverse`, `surface/brand-deep`, `surface/brand-subtle`, `text/inverse`, `text/brand`, each contrast-checked (50 pairs for a single brand).
- `color.status_roles`: point any status role (for example success) at your own hue, so a green brand can have a non-green success colour.
- Unused ramps are no longer generated: only the neutral and status ramps a brand or status role uses (a brand with one neutral no longer gets the default warm one).
- Optional third font role `ui` (navigation, buttons, list labels), for systems that pair two families by function rather than heading and body.
- 83 tests (from 74).

## 0.2.0

- Eight built-in dimensions that combine freely: brand, theme, device, platform, density, accessibility, locale and context (a marketing type scale).
- Brand with light and dark: brand palettes under a theme collection, with contrast checked for every brand in both.
- Layering: when dimensions overlap, the top layer carries the canonical token name and lower layers are prefixed.
- Custom dimensions for any other axis, and `extends` for a house of brands.
- Seven new presets.
- MIT license; capabilities guide; the packaged `.skill` moves to GitHub Releases.
- 74 tests (from 49).

## 0.1.0

- Guided interview with a sign-off gate, decision brief and decision records.
- Contrast-calibrated OKLCH colour ramps; semantic tokens for brand, theme and device.
- Contrast matrix, Figma build scripts, native variable JSON, phased build plan, DTCG tokens and a Style Dictionary config.
- Claude Code plugin, install scripts and a `.skill` package.
