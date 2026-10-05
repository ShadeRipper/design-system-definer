"""Decision brief (the playback the designer signs off) and decision records."""
from levers import LEVERS
from model import Alias

SYSTEM_WHY = {
    "single-brand-light-dark": "One brand that must work in light and dark; theme is the only axis of variation.",
    "multi-brand": "Several brands share one core; brand is a mode of one collection, never a separate collection.",
    "marketing-site": "One brand with expressive type; only the device varies.",
    "custom": "Dimensions were chosen directly.",
}
DIM_WHY = {
    "brand": ("Brand", "brands differ independently of device, so each brand is a mode"),
    "theme": ("Theme", "light and dark change the same roles with different values"),
    "device": ("Device", "spacing and type scale change with device, independent of brand or theme"),
}
RECORD_TEMPLATE = """# {title}

**Status:** accepted

## Context
{context}

## Decision
{decision}

## Alternatives considered
{alternatives}

## Consequences
{consequences}
"""


def _step(alias):
    return alias.target if isinstance(alias, Alias) else str(alias)


def _contrast_label(cfg):
    c = cfg["color"]["contrast"]
    name = next((k for k, v in {"AA": (4.5, 3.0), "AAA": (7.0, 4.5)}.items()
                 if (c["text"], c["ui"]) == v), "custom")
    return f"{name} (text {c['text']:g}:1, UI {c['ui']:g}:1)"


def build_brief(cfg, prims, collections, results):
    sem = next(c for c in collections if c.name in ("Brand", "Theme"))
    failing = [r for r in results if not r.passed]
    L = [f"# Decision brief", ""]
    L += [f"System type: **{cfg['system_type']}**. {SYSTEM_WHY.get(cfg['system_type'], SYSTEM_WHY['custom'])}", ""]
    L += ["## Structure", "", "| Collection | Modes | Why |", "| --- | --- | --- |",
          "| Primitives | Value | raw ramps and scales; never bound by components |"]
    for c in collections:
        if c.name == "Device":
            L.append(f"| Device | {', '.join(c.modes)} | {DIM_WHY['device'][1]} |")
        elif c.name == "Brand":
            L.append(f"| Brand | {', '.join(c.modes)} | {DIM_WHY['brand'][1]} |")
        elif c.name == "Theme":
            L.append(f"| Theme | {', '.join(c.modes)} | {DIM_WHY['theme'][1]} |")
    L.append("")
    if "brand" in cfg["dimensions"]:
        inc = cfg["base_mode"] == "include"
        L += [f"Base mode: **{'included' if inc else 'omitted'}**. " +
              ("A neutral, unbranded mode for defaults, docs and unknown-brand fallbacks."
               if inc else "Every product ships with one of the known brands, so no neutral fallback is needed."), ""]

    L += ["## Decisions", "", "| Decision | Value | Why |", "| --- | --- | --- |",
          f"| Contrast target | {_contrast_label(cfg)} | Every text and UI pair is checked in every mode; failures block export |",
          f"| Spacing base | {cfg['spacing']['base']}px | One unit keeps every gap a multiple of the same grid |",
          f"| Type scale | {', '.join(str(x) for x in cfg['type']['scale'])} | Primitive sizes; device tokens pick from it |",
          f"| Component tokens | {cfg['tiers']['component_tokens']} | Control height, icon size and special radii are decided now, not discovered mid-build |",
          "| Naming | lowercase slash paths, no spaces or brackets | Survives Figma and code export |", ""]

    L += ["## Brands", ""]
    for b in cfg["mode_brands"]:
        L.append(f"### {b['name']}")
        if b["anchors"]:
            for key, hexv in b["anchors"].items():
                r = prims.ramps[f"color/{b['slug']}/{key}"]
                where = (f"lands on step {r.anchor_step}" if r.anchor_on_ramp else
                         f"does not pass on white; ramp calibrated, pair with {r.safe_text} text")
                role = " (primary action)" if key == b["primary"] else ""
                L.append(f"- **{key}**{role}: `{hexv.upper()}` {where}")
        else:
            L.append("- no brand color: primary action uses the neutral ramp")
        L.append(f"- neutral: {b['neutral']}; fonts: {b['fonts']['heading']} / {b['fonts']['body']}; "
                 f"weights: {b['weights']['heading']} / {b['weights']['body']}")
        L.append(f"- shape: button {b['radius']['button']}, field {b['radius']['field']}, "
                 f"card {b['radius']['card']}, control {b['radius']['control']}; density: {b['density']}")
        for word in b.get("essence") or []:
            lev = LEVERS.get(str(word).lower())
            if lev:
                L.append(f"- *{word}* suggests: " + "; ".join(f"{k}: {v}" for k, v in lev.items()))
        if b.get("never"):
            L.append(f"- must never feel: {b['never']}")
        mode = b["name"] if sem.name == "Brand" else None
        if mode and mode in sem.modes:
            g = lambda p: _step(sem.get(p).values[mode])  # noqa: E731
            L.append(f"- derived: action fill `{g('color/action/primary/default')}`, text on it "
                     f"`{g('color/action/on-primary')}`, indicator `{g('color/indicator')}`")
        L.append("")
    if sem.name == "Theme":
        for mode in sem.modes:
            g = lambda p, mode=mode: _step(sem.get(p).values[mode])  # noqa: E731
            L.append(f"- {mode}: page `{g('color/surface/page')}`, action fill "
                     f"`{g('color/action/primary/default')}`, indicator `{g('color/indicator')}`")
        L.append("")

    L += ["## Accessibility", "",
          f"{len(results)} pairs checked, {len(failing)} failing."]
    for r in failing:
        L.append(f"- FAIL {r.id} ({r.mode}): {r.ratio:.2f}:1 < {r.required:g}:1"
                 + (f"; suggested fix {r.fix}" if r.fix else "; change the background, not the text"))
    if sem.notes:
        L += ["", "## Adjustments", ""] + [f"- {n}" for n in sem.notes]
    L += ["", "## Sign-off", "", "Nothing is written until this brief is approved. "
          "Reply with changes, or approve to generate the files.", ""]
    return "\n".join(L)


def build_records(cfg, prims, collections):
    sem = next(c for c in collections if c.name in ("Brand", "Theme"))
    rec = {}
    structure = ", ".join(f"{c.name} ({', '.join(c.modes)})" for c in collections)
    rec["01-collection-structure.md"] = RECORD_TEMPLATE.format(
        title="Collection and mode structure",
        context=f"The system varies along: {', '.join(cfg['dimensions']) or 'nothing'}.",
        decision=f"One collection per dimension: {structure}.",
        alternatives="- A collection per brand: rejected, forces a rebuild when a brand is added.\n"
                     "- Variables per brand inside one mode: rejected, no mode switching in Figma.",
        consequences="Adding a brand or theme is a new mode, not a restructure.")
    rec["02-contrast-target.md"] = RECORD_TEMPLATE.format(
        title="Contrast target", context="Text and UI colors must be readable in every mode.",
        decision=f"{_contrast_label(cfg)}. Ramp step 500 meets the UI target and step 600 the text target on white.",
        alternatives="- AA vs AAA vs custom ratios are all supported through `color.contrast`.",
        consequences="A failing pair blocks export. Contrast wins over anchor fidelity.")
    flagged = [(b["name"], k) for b in cfg["mode_brands"] for k in b["anchors"]
               if not prims.ramps[f"color/{b['slug']}/{k}"].anchor_on_ramp]
    rec["03-anchor-handling.md"] = RECORD_TEMPLATE.format(
        title="Brand anchors versus contrast",
        context="Brand colors are supplied as exact hex values.",
        decision="The exact hex is kept as a ramp step only if that step still meets its requirement; "
                 "otherwise the ramp is calibrated and the anchor is paired with a safe text color. "
                 + (f"Anchors that did not pass: {', '.join(f'{a} {k}' for a, k in flagged)}."
                    if flagged else "All anchors placed on the ramp."),
        alternatives="- Force the anchor onto step 500/600: rejected, fails WCAG for light brand colors.",
        consequences="The indicator (focus, selection) is a darker step than the action fill when the fill is light.")
    if "brand" in cfg["dimensions"]:
        inc = cfg["base_mode"] == "include"
        rec["04-base-mode.md"] = RECORD_TEMPLATE.format(
            title="Base mode", context="Multi-brand systems may need a neutral, unbranded mode.",
            decision="Base mode " + ("included." if inc else "omitted."),
            alternatives="- " + ("Omit it: every product ships with a known brand." if inc
                                 else "Include it: needed for white-label defaults and docs."),
            consequences="Components default to the first mode: " + sem.modes[0] + ".")
    rec["05-component-tokens.md"] = RECORD_TEMPLATE.format(
        title="Component-level tokens", context="Missing control height, round radius and track color "
        "were found only while building components in earlier projects.",
        decision=f"Tier `{cfg['tiers']['component_tokens']}`.",
        alternatives="- none: fewer variables, but the same discovery problem returns.\n"
                     "- full: component tokens for every part, more to maintain.",
        consequences="Components bind only to semantic or component tokens, never to primitives.")
    return rec
