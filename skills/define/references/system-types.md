# System types and dimensions

A type is defined by **what varies and how independently**, not by a label. The interview picks a type; the type sets the dimensions, collections, mode names and preset. Dimensions combine freely, and anything the built-in ones do not cover goes in `custom_dimensions`.

## Types

| Type | What varies | `dimensions` | Preset |
| --- | --- | --- | --- |
| Single brand, single theme | nothing | `[]` | none |
| Single brand, light/dark | theme | `[theme]` | `single-brand-light-dark` |
| Multi-brand / white-label | brand | `[brand, device]` | `multi-brand-white-label` |
| Multi-brand with light/dark | brand, theme | `[brand, theme, device]` | `brand-theme-white-label` |
| House of brands | sub-brands inherit a master | `[brand, device]` plus `extends:` | `house-of-brands` |
| Multi-platform | web, iOS, Android conventions | `[platform, theme]` | `multi-platform` |
| Responsive / multi-density | device, density | `[device, density]` | `responsive-density` |
| Product plus marketing | compact vs expressive type | `[device, context]` | `product-marketing` |
| Accessibility variants | large text, reduced motion | `[device, a11y, theme]` | `accessibility-variants` |
| Multi-locale | script, reading direction | `[device, locale]` | `multi-locale` |
| Web product plus marketing site | desktop and web now, room for more | `[device, platform, context]` | `web-product-and-site` |
| Marketing site | device only | `[device]` | `marketing-site` |
| Anything else | your own axes | any, plus `custom_dimensions` | none |

## What each dimension owns

| Dimension | Collection and modes | Tokens it owns |
| --- | --- | --- |
| `brand` | **Brand**: one mode per brand (plus **Base**). Always present; with no `brand` dimension it has one mode named after the brand | color roles (unless `theme` is on top), radius, border width, font family and weight, easing, spacing rhythm |
| `theme` | **Theme**: Light, Dark | color roles. With `brand` also on, brands supply palettes and Theme aliases them |
| `device` | **Device**: Mobile, Desktop (configurable) | spacing steps, margin, type sizes and line heights, control and icon size when `platform` is off |
| `platform` | **Platform**: Web, iOS, Android | control and icon size (44pt Apple, 48dp Material), motion durations |
| `density` | **Density**: Compact, Comfortable, Spacious | `space/inset`, `space/stack`, `space/section` |
| `a11y` | **A11y**: Default, Large text, Reduced motion | overrides of body-size type and line heights, focus-ring width, motion durations |
| `locale` | **Locale**: Latin, Japanese, Arabic (configurable) | font family per script, `layout/direction` |
| `context` | no collection | adds `type/size/marketing-*` tokens and `Marketing/*` text styles |
| custom | **your name** | whatever you list; each token aliases a primitive |

Without `device`, scale tokens (type sizes, spacing steps) live in the Brand collection at the first mode's values.

## Layering: how two dimensions vary the same token

When several dimensions vary one token, it is built as a chain. The **base layer** holds absolute values; each **override layer** aliases the layer below, or overrides it. The **top of the chain carries the canonical name** that components bind to. Lower layers are prefixed with their dimension (`device/type/size/body-m`, `palette/light/color/surface/page`), so names never collide in code export. Components never bind to prefixed names.

- Color with `brand` and `theme`: Brand holds `palette/light/...` and `palette/dark/...` per brand; Theme holds the canonical `color/...` roles aliasing them. A frame sets one Brand mode and one Theme mode.
- Type sizes: Device (base) then A11y. **Large text** enlarges only sizes that are the same in every device mode (body text); sizes that differ by device inherit, because Figma variables cannot do math.
- Font family: Brand (base) then Locale. Latin inherits; other scripts point at their own font.
- Durations: Platform (or Brand) then A11y; **Reduced motion** is 0.

## Choosing a structure

- Ask what varies **independently**. Two things that always change together are one dimension.
- `brand` plus `theme` multiplies the contrast checks (every brand in light and dark); this is fine, but say so.
- Prefer fewer dimensions. Figma limits modes per collection by plan.

## Base mode (multi-brand)

Base is a neutral, unbranded mode that every brand mode compares against and components fall back to.

- `include`: white-label systems (brand unknown until runtime); components need a default look in docs and tests.
- `none`: every product ships with one of the known brands (typical for a house of brands).
- `ask` (default): the interview asks once; the build refuses to run while it is still `ask`.

Base has no anchors; its primary action uses the neutral ramp. Override it with a top-level `base:` block.

## House of brands

A sub-brand lists `extends: <name>` and inherits every setting of that brand (anchors, fonts, radius, ...), overriding only what it sets. Each sub-brand is still one mode of Brand.

## Custom dimensions

For axes the built-in ones do not cover (season, region, tenant, ...):

```yaml
custom_dimensions:
  - name: Season
    modes: [Summer, Winter]
    tokens:
      space/season-gap:
        values: { Summer: space/16, Winter: space/24 }
```

Each value must be a primitive path (`space/16`, `color/white`); the build stops and says so if it is not. Add `type: color|number|string|boolean`, `scopes`, `description` as needed. Strings and booleans may be literals. A custom collection cannot reuse a built-in name.

## Limits worth knowing

- Per-script line height (CJK, Arabic) is not generated; add it as a custom dimension.
- High-contrast color is a contrast target (`contrast: AAA`), not a mode.
- Platform defaults (44 / 48, durations) are conventions; edit `platform:` to match your guidelines.
- Overrides cannot scale values that differ across lower modes (Figma has no variable math).
