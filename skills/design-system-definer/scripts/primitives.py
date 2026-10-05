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


def radius_key(v, cfg):
    return "full" if v == "full" else num(v)


def required_numbers(cfg):
    """Numeric values the semantic/device tiers will alias, by primitive kind."""
    dev, mode_brands = cfg["device"], cfg["mode_brands"]
    space = {m * cfg["spacing"]["base"] for m in cfg["spacing"]["scale"]}
    for vals in dev["space"].values():
        space |= set(vals)
    space |= set(dev["margin"])
    sizes = set(cfg["size"]["scale"]) | set(dev["control"]) | set(dev["icon"])
    font_sizes = set(cfg["type"]["scale"])
    lines = set(cfg["type"]["line_heights"])
    for t in dev["type"].values():
        font_sizes |= set(t["size"])
        lines |= set(t["line"])
    radius = set(cfg["radius"]["scale"])
    border = set(cfg["border"]["scale"])
    weights = set(cfg["type"]["weights"])
    families = {}
    for b in mode_brands:
        radius |= {v for v in b["radius"].values() if v != "full"}
        border |= set(b["border"].values())
        weights |= set(b["weights"].values())
        for fam in b["fonts"].values():
            families[slugify(fam)] = fam
    return {"space": space, "size": sizes, "font_size": font_sizes, "line": lines,
            "radius": radius, "border": border, "weight": weights, "family": families}


def build_primitives(cfg):
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

    req = required_numbers(cfg)
    for px in sorted(req["space"]):
        add(f"space/{num(px)}", "number", px, ["GAP"])
    for px in sorted(req["radius"]):
        add(f"radius/{num(px)}", "number", px, ["CORNER_RADIUS"])
    add("radius/full", "number", cfg["radius"]["full"], ["CORNER_RADIUS"], "Fully rounded")
    for px in sorted(req["border"]):
        add(f"border/{num(px)}", "number", px, ["STROKE_FLOAT"])
    for px in sorted(req["size"]):
        add(f"size/{num(px)}", "number", px, ["WIDTH_HEIGHT"])
    for px in sorted(req["font_size"]):
        add(f"font/size/{num(px)}", "number", px, ["FONT_SIZE"])
    for px in sorted(req["line"]):
        add(f"font/line-height/{num(px)}", "number", px, ["LINE_HEIGHT"])
    for w in sorted(req["weight"]):
        add(f"font/weight/{num(w)}", "number", w, ["FONT_WEIGHT"])
    for slug, fam in req["family"].items():
        add(f"font/family/{slug}", "string", fam, ["FONT_FAMILY"])
    return Primitives(col, results, notes, ramps, values)
