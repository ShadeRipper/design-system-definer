# Figma gotchas

Known API and import pitfalls; the build plan repeats them as a checklist.

- **Plain-hex colors are skipped on native import.** Use Figma's color-object format `{colorSpace, components, alpha, hex}`. The generator does.
- **Opacity on a variable-bound paint can reset to 100%.** Use layer opacity for translucency.
- **Shadow spread renders only with Clip content on.** Focus rings depend on it.
- **A text component property shares one default value across all variants.**
- **Cross-collection aliases:** Brand tokens may alias Device tokens; check both modes resolve. The `figma-build` scripts create these aliases and were exercised in a scratch file; native JSON import of cross-collection aliases is unverified, so prefer the scripts.
- **Names:** lowercase slash paths only. Spaces and brackets break code export.
- **Rate limits:** Figma MCP calls are limited by plan; build in the phases of `build-plan.md`, one component per call set.
- **Fonts:** brand fonts are often proprietary. Confirm the family is installed in the file or record a substitute. Text styles need the exact style name (`Semi Bold`, not `SemiBold`); the text-style script tries the common variants and reports the family it could not find.
- **Variable scopes:** never leave ALL_SCOPES on semantic tokens. The generator sets explicit scopes (`TEXT_FILL`, `STROKE_COLOR`, `GAP`, `CORNER_RADIUS`, ...) and empty scopes on primitives. EASING variables cannot take scopes.
- **Modes:** a new collection starts with one mode named `Mode 1`; the scripts rename it, then add the rest.
- **Idempotent reruns:** scripts reuse a collection and variables with the same name and update their values; they never delete. Remove stale variables by hand after renaming tokens.
- **Page context:** `use_figma` resets to the first page on every call; always load `figma-use` before calling it.
