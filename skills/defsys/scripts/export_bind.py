"""Scripts that bind an EXISTING Figma design to the generated tokens.

Run them through use_figma after the variables and text styles exist. They are generated from the
config, so they know your ramp names, role names, text styles, radius and spacing steps. Nothing is
hard-coded to one brand. Templates live in templates/bind/.

  01-bind-styles-colours-radius.js   text styles, colour variables, radius variables
  02-structure.js                    verified auto-layout, role names, spacing variables
  03-audit.js                        read-only coverage report
"""
import json
from pathlib import Path

from config import slugify
from export_figma import _resolve, text_style_defs

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "bind"
SPACE_SEMANTIC = ("xs", "sm", "md", "lg", "xl", "2xl")


def _key(col, var):
    return f"{col.name}::{var.path}"


def bind_config(cfg, collections):
    prim = next(c for c in collections if c.name == "Primitives")
    sem = [c for c in collections if c.name != "Primitives"]
    prim_paths = set(prim.paths())
    steps = list(cfg["color"]["steps"])

    def present(prefixes):
        return sorted(p for p in prefixes if f"{p}/{steps[0]}" in prim_paths)

    neutral = present(f"color/neutral-{slugify(k)}" for k in cfg["color"]["neutrals"])
    status = present(f"color/{slugify(k)}" for k in cfg["color"]["status"])
    brand = present({f"color/{b['slug']}/{a}" for b in cfg["mode_brands"] for a in b["anchors"]})

    # semantic colour roles, by path; a later collection (Theme over Brand) wins
    by_path = {}
    for col in sem:
        for v in col.variables:
            if v.type == "color" and v.path.startswith("color/"):
                by_path[v.path] = _key(col, v)
    surface = sorted(k for p, k in by_path.items()
                     if p.startswith("color/surface/") or p.startswith("color/action/primary/") or p.startswith("color/action/secondary/"))
    text = sorted(k for p, k in by_path.items() if p.startswith("color/text/") or p in ("color/action/on-primary", "color/on-indicator"))
    border = sorted(k for p, k in by_path.items() if p.startswith("color/border/") or p == "color/indicator")
    pick = lambda path: by_path.get(path, "")  # noqa: E731
    text_roles = {"primary": pick("color/text/primary"), "secondary": pick("color/text/secondary"),
                  "inverse": pick("color/text/inverse") or pick("color/text/primary"),
                  "onBrand": pick("color/text/on-brand") or pick("color/action/on-primary"),
                  "chromatic": [pick(f"color/text/{r}") for r in ("error", "success", "warning", "info", "brand") if pick(f"color/text/{r}")]}

    # radius: primitive steps by value, plus the semantic roles and their values
    def number(col, var):
        return _resolve(collections, col, var)

    r_prim = {}
    for v in prim.variables:
        if v.path.startswith("radius/") and v.path[len("radius/"):].isdigit():
            r_prim[str(int(number(prim, v)))] = _key(prim, v)
    radius = {"prim": r_prim, "round": ""}
    for col in sem:
        for v in col.variables:
            if v.path == "radius/round":
                radius["round"] = _key(col, v)
            for role in ("button", "field", "card", "control"):
                if v.path == f"radius/{role}":
                    radius[role] = _key(col, v)
                    radius[role + "Value"] = int(number(col, v))
    if not radius["round"] and "radius/full" in prim_paths:
        radius["round"] = f"Primitives::radius/full"

    # spacing: semantic steps first, then primitive steps for values with no semantic step
    space = {}
    for col in sem:
        for v in col.variables:
            if v.type == "number" and (v.path.startswith("space/") or v.path == "layout/margin") and "GAP" in (v.scopes or []):
                val = number(col, v)
                if isinstance(val, (int, float)) and val > 0:
                    space.setdefault(str(round(val, 2)).rstrip("0").rstrip("."), _key(col, v))
    for v in prim.variables:
        if v.path.startswith("space/") and v.path[len("space/"):].isdigit() and int(v.path[6:]) > 0:
            space.setdefault(str(int(number(prim, v))), _key(prim, v))

    styles = []
    for d in text_style_defs(collections, cfg):
        ui = d["bind"]["family"].endswith("/ui")
        styles.append({"name": d["name"], "size": d["size"], "family": d["family"], "weight": d["weight"], "role": "ui" if ui else "text"})
    ui_family = next((s["family"] for s in styles if s["role"] == "ui"), None)
    return {"primitives": "Primitives", "steps": steps, "ramps": {"neutral": neutral, "brand": brand, "status": status},
            "roles": {"surface": surface, "text": text, "border": border, "actionDefault": pick("color/action/primary/default")},
            "textRoles": text_roles, "radius": radius, "space": space, "styles": styles, "uiFamily": ui_family}


RUN_HEADER = (
    "// RUN HEADER: set these, then run the whole file through use_figma.\n"
    "const PAGE_ID = 'REPLACE_WITH_PAGE_ID';        // the page that holds the screens\n"
    "const ROOT_IDS = ['REPLACE_WITH_FRAME_ID'];    // the frames or sections to process (a few thousand layers per call)\n"
    "const APPLY_FLAG = false;                      // false = dry run, reports and writes nothing; true = apply\n")


def _read(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def _script(title, body, config, options=False):
    head = f"// Design System Definer: {title}\n" + RUN_HEADER
    if options:
        head += "const OPTIONS = {layout: true, names: true, spacing: true};   // switch parts off if you want to run them separately\n"
    return head + "const CONFIG = " + json.dumps(config, ensure_ascii=False, sort_keys=True) + ";\n" + _read("common.js") + _read(body)


README = """# Bind an existing design to the tokens

Generated from your config. Run these through `use_figma` (with the `figma-use` skill loaded) after the
variables and text styles exist in the file.

1. Save a named version in Figma first (File, Save to version history). Scripts cannot do this.
2. Open each script and set the three lines under RUN HEADER.
3. **Dry run first** (`APPLY_FLAG = false`). Read the counts and the unbound lists.
4. **Pilot on one frame per section**, then compare screenshots before and after. A binding pass should
   change almost no pixels; auto-layout and spacing passes should change none.
5. Apply in batches of about 1,500 to 2,500 layers per call; frames can run as parallel calls.
6. Run `03-audit.js` (read-only) for the measured coverage, before and after.

Order: `01`, then `02`, then `03`. To see what an existing file uses *before* you define anything, run `templates/inventory.js` from the skill (no config needed).

What is skipped on purpose: layers inside instances (they belong to another library or component),
text that needs uppercase or underline (a style would reset it), italic text, large regular-weight
headings when there is no regular-weight heading style, colours with no close match, and any
auto-layout conversion that would move a child by more than 1px.
"""


def export_bind_scripts(cfg, collections):
    config = bind_config(cfg, collections)
    return {"01-bind-styles-colours-radius.js": _script("bind text styles, colours and radius", "bind-styles-colours-radius.js", config),
            "02-structure.js": _script("structure: auto-layout, names, spacing", "structure.js", config, options=True),
            "03-audit.js": _script("audit: read-only coverage report", "audit.js", config),
            "README.md": README}
