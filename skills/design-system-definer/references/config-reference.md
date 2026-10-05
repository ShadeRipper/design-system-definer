# Config reference (`ds.config.yaml`)

Override order, later wins: skill defaults, preset, project config. Full working example: `examples/multi-brand-sample.yaml`. A minimal single brand:

```yaml
preset: single-brand-light-dark
brands:
  - name: Acme
    anchors: { blue: "#2563EB" }
```

## Top level

| Key | Default | Meaning |
| --- | --- | --- |
| `preset` | none | one of the files in `presets/` (single-brand-light-dark, multi-brand-white-label, brand-theme-white-label, house-of-brands, multi-platform, responsive-density, product-marketing, accessibility-variants, multi-locale, marketing-site) |
| `system_type` | custom | label shown in the brief |
| `dimensions` | from preset, else `[brand]` if more than one brand | any of `brand`, `theme`, `device`, `platform`, `density`, `a11y`, `context`, `locale`; combine freely |
| `base_mode` | `ask` | `include` or `none`; must be decided when `brand` is a dimension |
| `base` | `{}` | overrides for the Base mode (fonts, radius, weights, ...) |
| `brands` | required | list, see below |
| `outputs` | figma, dtcg, decision-records, build-plan | which optional outputs to write |
| `components` | button, text-field, checkbox, radio, selectable-card, progress, feedback | handed to the build plan |
| `tiers.component_tokens` | `minimal` | `none`, `minimal`, `full` |

## Brand

| Key | Default | Meaning |
| --- | --- | --- |
| `name` | required | also the mode name |
| `slug` | slugified name | token path segment |
| `anchors` | `{}` | `{name: "#hex"}`; each becomes a ramp `color/<slug>/<name>/<step>` |
| `primary` | first anchor, else `neutral` | the anchor that drives primary actions |
| `neutral` | first of `color.neutrals` | `warm`, `cool`, or your own name |
| `fonts` | Inter | `{heading, body}`; body defaults to heading |
| `weights` | 600 / 400 | `{heading, body}` |
| `radius` | 8 / 8 / 8 / 4 | `{button, field, card, control}` in px or `full` |
| `border` | 1 / 2 | `{default, focus}` px |
| `density` | `default` | `roomy` uses larger section and stack gaps |
| `easing` | `[0.5, 0, 0.5, 1]` | cubic bezier |
| `essence`, `never` | none | shown in the brief with suggested levers |

## color

| Key | Default |
| --- | --- |
| `contrast` | `AA`; or `AAA`; or `{text: 4.5, ui: 3.0}` |
| `steps` | 50, 100, ..., 900, 950 (must include 500 and 600) |
| `neutrals` | `{cool: "#64748B", warm: "#78716C"}` |
| `status` | red `#DC2626`, green `#16A34A`, amber `#D97706`, blue `#2563EB` |

## Scales and device

`spacing: {base: 4, scale: [multipliers]}` · `radius: {scale: [...], full: 9999}` · `border: {scale}` · `size: {scale}` · `type: {scale, line_heights, weights, styles}` where `styles` is `[name, size-token, family-role, weight-role]` rows (defaults give Heading/Display..Label/S).

`device: {modes: [Mobile, Desktop], space: {xs: [4, 4], ...}, type: {display: {size: [32, 48], line: [40, 56]}, ...}, margin: [16, 40], control: [48, 48], icon: [20, 20]}`. Every value needs one entry per device mode. Any px value used is added to the primitives automatically.

## Other dimensions

```yaml
platform:  { modes: [Web, iOS, Android], control: [44, 44, 48], icon: [20, 24, 24],
             duration: { short: [150, 200, 100], medium: [250, 350, 250], long: [400, 500, 300] } }
density:   { modes: [Compact, Comfortable, Spacious], inset: [8, 12, 16], stack: [8, 16, 24], section: [24, 32, 48] }
a11y:      { large_text_scale: 1.25, large_focus_width: 3 }   # modes are fixed: Default, Large text, Reduced motion
locale:    { modes: [Latin, Japanese, Arabic], families: { Japanese: Noto Sans JP, Arabic: Noto Sans Arabic },
             direction: { Arabic: rtl } }                      # the first mode inherits the brand fonts
context:   { marketing_type: { display-xl: { size: [40, 72], line: [48, 80] } } }
motion:    { duration: { short: 150, medium: 250, long: 400 } }  # used when `platform` is off
```

Every list needs one entry per mode of its dimension. `context` adds `type/size/marketing-*` tokens and `Marketing/*` text styles; it creates no collection.

## House of brands and custom dimensions

A brand with `extends: <name>` inherits every setting of that brand and overrides only what it sets. `custom_dimensions` adds your own collections; see [system-types.md](system-types.md#custom-dimensions).
