# Changelog

Versions follow [semantic versioning](https://semver.org). Below 1.0, a minor bump (0.x) adds capability and may change details; a patch bump (0.x.y) is fixes only.

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
