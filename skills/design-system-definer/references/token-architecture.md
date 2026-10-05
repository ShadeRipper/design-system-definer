# Token architecture

Three tiers, each in its own collection:

1. **Primitives** (single mode `Value`): raw ramps and scales. Never bound by components or text styles. Variables have empty scopes, so they do not appear in pickers.
2. **Device** (modes Mobile, Desktop): t-shirt spacing, type sizes, line heights, margin, control and icon sizes. Aliases to primitives.
3. **Brand** or **Theme** (one mode per brand or theme): semantic roles. Aliases to primitives or Device. Components bind here only.

**Alias-only rule:** in the semantic tier every color, number and string is an alias. Only easing curves are literals.

## Primitive names

`color/white`, `color/black` · `color/neutral-<temp>/<step>` · `color/<hue>/<step>` for status (`red`, `green`, `amber`, `blue`) · `color/<brand-slug>/<anchor-name>/<step>` · `space/<px>` · `radius/<px>`, `radius/full` · `border/<px>` · `size/<px>` · `font/size/<px>` · `font/line-height/<px>` · `font/weight/<n>` · `font/family/<slug>`.

Steps default to 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950. Every anchor also exists, unaltered, as the ramp step it lands on when it passes contrast. Numeric scales are the configured scale unioned with every value the semantic tiers use, so an alias never points at nothing.

## Semantic roles

Action: `color/action/primary/{default,hover,pressed,border}`, `color/action/on-primary`, `color/action/secondary/{hover,pressed}`.
Surface: `color/surface/{brand,page,card,disabled,error,success,warning,info,track}`.
Text: `color/text/{primary,secondary,disabled,error,success,warning,info,on-brand}`.
Border: `color/border/{default,strong,subtle,error,success,warning,info}`.
Indicator: `color/indicator`, `color/on-indicator` (focus, selection, progress; see accessibility).
Shape and rhythm: `radius/{button,field,card,control,round}`, `border-width/{default,focus}`, `space/{section,stack}`.
Type: `type/family/{heading,body}`, `type/weight/{heading,body}`, device `type/size/*`, `type/line-height/*`.
Motion: `easing/standard` (literal cubic bezier).

Component-token tier (`tiers.component_tokens`): `none` drops `radius/control`, `radius/round`, `size/control`, `size/icon`; `minimal` (default) keeps them; `full` adds `component/{button,field}/height`, `component/checkbox/size`, `component/progress/height`.

## Deriving collections

One collection per independent dimension; modes are the values of that dimension. Brands are never separate collections. See [system-types.md](system-types.md).

## Naming rules

Lowercase slash paths; segments are letters, digits and single hyphens. Spaces, brackets and capitals are rejected: they break code export. Brand slugs default to the slugified name (`Lay's` becomes `lays`); set `slug:` to choose (`sbux`).
