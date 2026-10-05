"""Phased Figma build plan for the figma-generate-library and figma-use skills."""

COMPONENT_TOKENS = {
    "button": ["color/action/primary/default", "color/action/primary/hover", "color/action/primary/pressed",
               "color/action/primary/border", "color/action/on-primary", "color/action/secondary/hover",
               "color/action/secondary/pressed", "radius/button", "size/control", "border-width/default",
               "color/surface/disabled", "color/text/disabled", "color/indicator", "border-width/focus"],
    "text-field": ["color/surface/card", "color/border/default", "color/border/error", "color/text/primary",
                   "color/text/secondary", "color/text/error", "radius/field", "size/control",
                   "color/surface/disabled", "color/text/disabled", "color/indicator", "border-width/focus"],
    "checkbox": ["color/border/default", "color/indicator", "color/on-indicator", "radius/control",
                 "size/icon", "color/text/primary", "border-width/default"],
    "radio": ["color/border/default", "color/indicator", "color/on-indicator", "radius/round",
              "size/icon", "color/text/primary"],
    "selectable-card": ["color/surface/card", "color/border/default", "color/indicator", "radius/card",
                        "space/stack", "color/text/primary", "color/text/secondary"],
    "progress": ["color/surface/track", "color/indicator", "radius/round"],
    "feedback": [f"color/{k}/{r}" for r in ("error", "success", "warning", "info") for k in ("surface", "text", "border")]
                + ["radius/card", "space/stack"],
}

GOTCHAS = [
    "Colors import only as color objects; plain hex strings are skipped.",
    "Opacity on a variable-bound paint can reset to 100%: use layer opacity for translucency.",
    "Shadow spread renders only with Clip content on; focus rings depend on it.",
    "A text component property shares one default value across all variants.",
    "Brand tokens may alias Device tokens across collections; check that both modes resolve.",
    "Names must be lowercase slash paths: spaces and brackets break code export.",
    "Figma MCP calls are rate-limited by plan: build in the phases below, not in one run.",
    "Brand fonts are often proprietary: confirm the family is installed or use the recorded substitute.",
]


def build_plan(cfg, collections, script_names):
    sem = next(c for c in collections if c.name in ("Brand", "Theme"))
    counts = ", ".join(f"{c.name}: {len(c.modes)} mode(s), {len(c.variables)} variables" for c in collections)
    fonts = sorted({b["fonts"][r] for b in cfg["mode_brands"] for r in ("heading", "body")})
    L = ["# Figma build plan", "",
         "Skills used: `figma-use` (mandatory before every `use_figma` call) and `figma-generate-library` "
         "for components. Stop at every checkpoint and let the designer review.", "",
         "## Phase 0: pre-flight", "",
         f"- [ ] New or empty Figma design file; note its file key.",
         f"- [ ] Fonts available in the file: {', '.join(fonts)} (else record a substitute).",
         "- [ ] Read `figma-gotchas` below before starting.", "",
         "## Phase 1: foundations", ""]
    for i, name in enumerate(script_names, 1):
        if name.endswith("text-styles.js"):
            continue
        L.append(f"- [ ] {i}. Run `figma-build/{name}` with `use_figma`; confirm `errors` is empty.")
    L += [f"- [ ] Verify in the Variables panel: {counts}.",
          "- [ ] Every semantic variable has a description and explicit scopes; no variable is ALL_SCOPES.",
          "",
          "**CHECKPOINT 1 (human):** designer reviews the Variables panel, every mode, and "
          "`contrast-matrix.md`. Do not continue until approved.", "",
          "## Phase 2: text styles", ""]
    if any(n.endswith("text-styles.js") for n in script_names):
        L.append("- [ ] Run the text-styles script; every style is bound to size, line height, family and weight variables.")
    L += ["", "**CHECKPOINT 2 (human):** switch the frame mode through every "
          f"{sem.name} mode and confirm the type changes.", "", "## Phase 3: components", "",
          "One component per call set. Bind only to the tokens listed; never to primitives.", ""]
    have = {v.path for c in collections for v in c.variables}
    for comp in cfg["components"]:
        toks = [t for t in COMPONENT_TOKENS.get(comp, []) if t in have]
        L += [f"### {comp}", "", f"- [ ] Build with `figma-generate-library`: variants, states, auto layout.",
              f"- [ ] Bind: {', '.join('`' + t + '`' for t in toks) if toks else '(no tokens mapped; define them in the config)'}",
              f"- [ ] Check every {sem.name} mode in a screenshot.", "",
              f"**CHECKPOINT ({comp}):** designer approves before the next component.", ""]
    L += ["## Phase 4: hand-off", "",
          "- [ ] Download the `.fig` file and import it into Claude Design. If modes or descriptions are "
          "flattened, add the `dtcg/` folder to Claude Design instead.",
          "- [ ] Code (optional): `dtcg/tokens` plus `dtcg/sd.config.mjs` with Style Dictionary.", "",
          "## Figma gotchas", ""] + [f"- [ ] {g}" for g in GOTCHAS] + [""]
    return "\n".join(L)
