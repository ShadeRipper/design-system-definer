"""Primitive tier: contrast-calibrated ramps plus numeric scales and font families.

Numeric scales are the configured scale unioned with every value the semantic and
device tiers reference, so a semantic alias can never point at a missing primitive.
"""
import re
from dataclasses import dataclass, field

from config import slugify
from contrast import check_pair
from model import Collection, Variable
from ramps import BLACK, WHITE, generate_ramp

NAME_SEGMENT = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PRIMITIVE_MODE = "Value"


@dataclass
class Primitives:
    collection: Collection
    results: list  # contrast PairResult list (ramp conformance)
    notes: list
    ramps: dict  # path prefix -> Ramp
    values: dict = field(default_factory=dict)  # path -> literal (hex, number, string)


def validate_path(path):
    for seg in path.split("/"):
        if not NAME_SEGMENT.match(seg):
            raise ValueError(f"token name segment {seg!r} in {path!r} must be lowercase "
                             "letters, digits and single hyphens (no spaces or brackets)")


def num(x):
    """Name form of a number: 16 -> '16', 0.5 -> '0-5'."""
    x = int(x) if float(x) == int(x) else x
    return str(x).replace(".", "-")


def prim_path(kind, value):
    """Primitive path for a ("prim", kind, value) spec."""
    if kind == "radius":
        return "radius/full" if value == "full" else f"radius/{num(value)}"
    if kind == "family":
        return f"font/family/{slugify(value)}"
    prefix = {"space": "space", "border": "border", "size": "size", "font_size": "font/size",
              "line": "font/line-height", "weight": "font/weight", "duration": "duration"}[kind]
    return f"{prefix}/{num(value)}"


def base_scales(cfg):
    """Configured scales; the semantic plan's values are unioned in by build_primitives."""
    return {"space": {m * cfg["spacing"]["base"] for m in cfg["spacing"]["scale"]},
            "size": set(cfg["size"]["scale"]), "font_size": set(cfg["type"]["scale"]),
            "line": set(cfg["type"]["line_heights"]), "radius": set(cfg["radius"]["scale"]),
            "border": set(cfg["border"]["scale"]), "weight": set(cfg["type"]["weights"]),
            "duration": set(), "family": {}}


def build_primitives(cfg, needed=None):
    col = Collection("Primitives", [PRIMITIVE_MODE])
    results, notes, ramps, values = [], [], {}, {}
    color = cfg["color"]
    targets, steps = color["contrast"], color["steps"]

    def add(path, vtype, value, scopes, description=""):
        validate_path(path)
        if path in values:
            raise ValueError(f"duplicate token path {path}")
        if vtype == "number" and float(value) == int(value):
            value = int(value)
        values[path] = value
        col.variables.append(Variable(path, vtype, {PRIMITIVE_MODE: value}, scopes, description))

    add("color/white", "color", WHITE, [])
    add("color/black", "color", BLACK, [])

    def add_ramp(prefix, label, anchor_hex, description):
        ramp = generate_ramp(anchor_hex, steps, ui=targets["ui"], text=targets["text"])
        ramps[prefix] = ramp
        for s in steps:
            add(f"{prefix}/{s}", "color", ramp.steps[s], [], description)
        results.append(check_pair(f"{label} 500 on white", "primitives", "ui",
                                  ramp.steps[500], WHITE, targets))
        results.append(check_pair(f"{label} 600 on white", "primitives", "text",
                                  ramp.steps[600], WHITE, targets))
        for n in ramp.notes:
            notes.append(f"{label}: {n}")
        if ramp.anchor_on_ramp:
            notes.append(f"{label}: anchor {ramp.anchor} placed on step {ramp.anchor_step}")
        best = max(ramp.anchor_contrast_white, ramp.anchor_contrast_black)
        if best < targets["text"]:
            notes.append(f"{label}: anchor {ramp.anchor} cannot carry text at {targets['text']:g}:1 "
                         f"(best {best:.2f}:1 with {ramp.safe_text}); use a darker ramp step as the fill")

    for name, hexv in color["neutrals"].items():
        add_ramp(f"color/neutral-{slugify(name)}", f"neutral-{name}", hexv,
                 f"Neutral ramp ({name}), calibrated to the contrast target")
    for name, hexv in color["status"].items():
        add_ramp(f"color/{slugify(name)}", name, hexv, f"Status ramp ({name})")
    seen_brands = set()
    for b in cfg["mode_brands"]:
        if b["slug"] in seen_brands:
            continue
        seen_brands.add(b["slug"])
        for key, hexv in b["anchors"].items():
            add_ramp(f"color/{b['slug']}/{key}", f"{b['name']} {key}", hexv,
                     f"{b['name']} {key} ramp; anchor {hexv.upper()}")

    req = base_scales(cfg)
    for kind, vals in (needed or {}).items():
        if kind == "family":
            req["family"].update(vals)
        else:
            req[kind] |= {v for v in vals if v != "full"}
    scopes = {"space": ["GAP"], "radius": ["CORNER_RADIUS"], "border": ["STROKE_FLOAT"],
              "size": ["WIDTH_HEIGHT"], "font_size": ["FONT_SIZE"], "line": ["LINE_HEIGHT"],
              "weight": ["FONT_WEIGHT"], "duration": []}
    for kind in ("space", "radius", "border", "size", "font_size", "line", "weight", "duration"):
        for v in sorted(req[kind]):
            add(prim_path(kind, v), "number", v, scopes[kind], "")
    add("radius/full", "number", cfg["radius"]["full"], ["CORNER_RADIUS"], "Fully rounded")
    for slug, fam in sorted(req["family"].items()):
        add(f"font/family/{slug}", "string", fam, ["FONT_FAMILY"])
    return Primitives(col, results, notes, ramps, values)
