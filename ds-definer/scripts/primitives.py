"""Build the primitive token tier (ramps, spacing, radius, type) from a config."""
import re
from dataclasses import dataclass

from config import slugify
from contrast import check_pair
from ramps import BLACK, WHITE, generate_ramp

NAME_SEGMENT = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass
class Token:
    path: str  # lowercase slash path, e.g. color/lays/primary/500
    type: str  # "color" | "number" | "string"
    value: object  # hex string, number, or string
    description: str = ""


def validate_path(path):
    for seg in path.split("/"):
        if not NAME_SEGMENT.match(seg):
            raise ValueError(f"token name segment {seg!r} in {path!r} must be lowercase "
                             "letters, digits and single hyphens (no spaces or brackets)")


def _num_name(x):
    return str(x).replace(".", "-")


def build_primitives(cfg):
    """Return (tokens, contrast_results, notes)."""
    tokens, results, notes = [], [], []
    color, targets = cfg["color"], cfg["color"]["contrast"]
    steps = color["steps"]

    tokens += [Token("color/white", "color", WHITE), Token("color/black", "color", BLACK)]

    def add_ramp(prefix, label, anchor_hex):
        ramp = generate_ramp(anchor_hex, steps, ui=targets["ui"], text=targets["text"])
        for s in steps:
            tokens.append(Token(f"{prefix}/{s}", "color", ramp.steps[s]))
        tokens.append(Token(f"{prefix}/anchor", "color", ramp.anchor,
                            "Exact brand color as supplied; not guaranteed to pass on white"))
        results.append(check_pair(f"{label} 500 on white", "primitives", "ui",
                                  ramp.steps[500], WHITE, targets))
        results.append(check_pair(f"{label} 600 on white", "primitives", "text",
                                  ramp.steps[600], WHITE, targets))
        for n in ramp.notes:
            notes.append(f"{label}: {n}")
        if ramp.anchor_on_ramp:
            notes.append(f"{label}: anchor {ramp.anchor} placed on step {ramp.anchor_step}")
        # Advisory only: whether the anchor itself can carry text. It is not a blocking
        # pair until a semantic token actually uses the anchor as a background.
        best = max(ramp.anchor_contrast_white, ramp.anchor_contrast_black)
        if best < targets["text"]:
            notes.append(f"{label}: anchor {ramp.anchor} cannot carry text at {targets['text']:g}:1 "
                         f"(best {best:.2f}:1 with {ramp.safe_text}); use a darker ramp step as the fill")

    add_ramp("color/neutral", "neutral", color["neutral"])
    for brand in cfg["brands"]:
        for role, hexv in brand["anchors"].items():
            add_ramp(f"color/{brand['slug']}/{slugify(role)}", f"{brand['name']} {role}", hexv)

    base = cfg["spacing"]["base"]
    for m in cfg["spacing"]["scale"]:
        tokens.append(Token(f"spacing/{_num_name(m)}", "number", m * base))
    for name, px in cfg["radius"].items():
        tokens.append(Token(f"radius/{slugify(name)}", "number", px))
    for px in cfg["type"]["scale"]:
        tokens.append(Token(f"font/size/{_num_name(px)}", "number", px))
    for name, w in cfg["type"]["weights"].items():
        tokens.append(Token(f"font/weight/{slugify(name)}", "number", w))
    for brand in cfg["brands"]:
        for role, family in (brand.get("fonts") or {}).items():
            tokens.append(Token(f"font/family/{brand['slug']}/{slugify(role)}", "string", family))

    seen = set()
    for t in tokens:
        validate_path(t.path)
        if t.path in seen:
            raise ValueError(f"duplicate token path {t.path}")
        seen.add(t.path)
    return tokens, results, notes
