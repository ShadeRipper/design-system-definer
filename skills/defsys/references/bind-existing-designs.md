# Binding an existing design to the tokens

Use this when the Figma file already has screens. The skill generates scripts from your config; they bind text styles, colours, radius and spacing, name layers and add auto-layout where it is safe. Enable with `outputs: [figma, dtcg, decision-records, build-plan, bind]`; scripts land in `figma-bind/`.

## Method

1. **Variables and text styles first.** Run `figma-build/` so the tokens exist in the file.
2. **Save a named version** in Figma. Scripts cannot.
3. **Dry run** `01-bind-styles-colours-radius.js` (`APPLY_FLAG = false`). Read the counts and the unbound lists. Decide what the system is missing before applying (see "Gaps a dry run finds").
4. **Pilot one frame per section.** Take screenshots before and after and compare pixels. A binding pass should change almost nothing; auto-layout and spacing passes should change nothing.
5. **Apply in batches** of about 1,500 to 2,500 layers per call. Independent frames can run as parallel calls.
6. **Structure pass** `02-structure.js` the same way: dry run, pilot, batches.
7. Read the unbound lists. Those are decisions, not failures.

## What the scripts decide

| Layer | Rule |
| --- | --- |
| Text style | Same family role (the `ui` family only for small text), weight class (strong at 600 and up, or 500 on a short label), nearest size. Sizes under the smallest style snap up to it |
| Text colour | Neutrals by lightness (dark = primary, mid = secondary, near-white = inverse); chromatic text goes to the nearest status role; text on a brand fill becomes on-brand text |
| Fill and stroke | Nearest colour in Lab among the semantic roles and the ramps, semantic preferred, within a tolerance. Thin rectangles use border roles; icons may use text roles |
| Radius | Exact matches to the radius steps; a role (button, field, card) only when the layer name or size suggests it; pills to the round role |
| Spacing | Exact matches only, on auto-layout frames. Off-grid values are listed, never snapped |
| Names | Only default names (`Frame 12`, `Group`, `div.x`) are replaced, by role |
| Auto-layout | Only a clean row or column. Every conversion is verified and rolled back if any child moves more than 1px |

Skipped on purpose: layers inside instances; text that needs uppercase or underline; italic; large regular-weight headings when no regular-weight heading style exists; colours with no close match; groups with masks or effects.

## Gaps a dry run finds

Expect these and decide before applying:

- **Dark surfaces.** If the file uses white text on dark panels, the system needs inverse roles. They exist: `surface/inverse`, `surface/brand-deep`, `text/inverse`.
- **Emphasis weights.** Body text in Medium or Bold needs Strong variants of the body styles (Inter 600 at body sizes).
- **Regular-weight headings.** Large display text in Regular needs Regular-weight display styles, or those layers stay unstyled.
- **Third font role.** If one family sets navigation and buttons and another sets content, set `fonts.ui`.
- **Chart or illustration colours** have no role in a UI token system; they stay unbound.

## Gotchas (each one cost a real regression)

1. **A paint bound to a variable and given an opacity in the same assignment resets to 100%.** Bind first, then set opacity in a second assignment on a clone of `node.fills`. Missing this made a hidden border and a shadow rectangle opaque.
2. **Setting `letterSpacing`, even to its default, detaches a text style.** Let the style win; skip layers that depend on case or underline.
3. **Fixed-width text boxes wrap at new sizes.** Try hug-width; keep it if the box grew, revert if not.
4. **Reparenting and layout conversion can shift children.** Compare absolute positions before and after.
5. **Slate greys have a Lab chroma near 16.** Treat chroma under 22 as neutral or they are read as a status colour.
6. **A gradient background must be averaged, not treated as an image.**
7. **Fonts that are not installed throw on `loadFontAsync`.** Catch and skip; report them.
8. **Switch pages once per call.**

## Delta builds

After changing the config, rebuild with `--previous <old build folder>`. `figma-build-delta/` then holds only new or changed variables and styles, so the second run in Figma is small. Scripts never delete; removed items are listed in its README.
