"""Figma native variable JSON (one file per collection and mode).

Colors are color objects (colorSpace, components, alpha, hex); Figma silently
skips plain hex strings on import.
NOTE: structure follows Figma's DTCG-style export but is NOT yet validated
against a real Figma export fixture (PRD R6).
"""
import json

from color import hex_to_srgb_floats


def nest(tokens, leaf):
    root = {}
    for t in tokens:
        node = root
        *groups, name = t.path.split("/")
        for g in groups:
            node = node.setdefault(g, {})
        node[name] = leaf(t)
    return root


def _leaf(t):
    if t.type == "color":
        value = {"colorSpace": "srgb",
                 "components": [round(c, 5) for c in hex_to_srgb_floats(t.value)],
                 "alpha": 1, "hex": t.value}
    else:
        value = t.value
    return {"$type": t.type, "$value": value, "$description": t.description}


def export_figma(tokens, collection="Primitives", mode="Value"):
    """Return {filename: json_text}."""
    body = json.dumps(nest(tokens, _leaf), indent=2, ensure_ascii=False)
    return {f"{collection}.{mode}.tokens.json": body + "\n"}
