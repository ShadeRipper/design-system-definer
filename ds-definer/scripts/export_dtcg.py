"""DTCG (Design Tokens Community Group, 2025.10) token export."""
import json

from color import hex_to_srgb_floats
from export_figma import nest

DIMENSION_PREFIXES = ("spacing/", "radius/", "font/size/")


def _leaf(t):
    if t.type == "color":
        return {"$type": "color",
                "$value": {"colorSpace": "srgb",
                           "components": [round(c, 5) for c in hex_to_srgb_floats(t.value)],
                           "hex": t.value},
                "$description": t.description}
    if t.path.startswith(DIMENSION_PREFIXES):
        return {"$type": "dimension", "$value": {"value": t.value, "unit": "px"}}
    if t.path.startswith("font/weight/"):
        return {"$type": "fontWeight", "$value": t.value}
    if t.path.startswith("font/family/"):
        return {"$type": "fontFamily", "$value": t.value}
    return {"$type": "number", "$value": t.value}


def export_dtcg(tokens):
    return json.dumps(nest(tokens, _leaf), indent=2, ensure_ascii=False) + "\n"
