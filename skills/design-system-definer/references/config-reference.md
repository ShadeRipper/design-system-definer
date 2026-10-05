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
| `preset` | none | `single-brand-light-dark`, `multi-brand-white-label`, `marketing-site` |
| `system_type` | custom | label shown in the brief |
| `dimensions` | from preset, else `[brand]` if more than one brand | any of `brand`, `theme`, `device` (`brand` + `theme` rejected) |
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
