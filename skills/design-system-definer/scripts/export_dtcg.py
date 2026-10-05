"""DTCG (Design Tokens Community Group, 2025.10) export and a Style Dictionary config.

Files are written per collection and mode (DTCG has no modes). Aliases use the
`{group.token}` form, so Style Dictionary can resolve them across the merged sources.
"""
import json

from color import hex_to_srgb_floats
from config import slugify
from export_figma import _nest
from model import Alias

DIMENSION = ("space/", "radius/", "border/", "size/", "font/size/", "font/line-height/",
             "layout/", "border-width/", "type/size/", "type/line-height/", "component/")


def _leaf(v, mode):
    val = v.values[mode]
    desc = {"$description": v.description} if v.description else {}
    if isinstance(val, Alias):
        ref = "{" + val.target.replace("/", ".") + "}"
        return {"$value": ref, **desc}  # type is inherited from the target
    if v.type == "color":
        return {"$type": "color", "$value": {"colorSpace": "srgb",
                "components": [round(c, 5) for c in hex_to_srgb_floats(val)], "hex": val}, **desc}
    if v.type == "easing":
        return {"$type": "cubicBezier", "$value": list(val), **desc}
    if v.type == "string":
        return {"$type": "fontFamily", "$value": val, **desc}
    if "weight" in v.path:
        return {"$type": "fontWeight", "$value": val, **desc}
    if v.path.startswith(DIMENSION):
        return {"$type": "dimension", "$value": {"value": val, "unit": "px"}, **desc}
    return {"$type": "number", "$value": val, **desc}


def export_dtcg(collections):
    files = {}
    for col in collections:
        for mode in col.modes:
            name = f"{col.name}.tokens.json" if len(col.modes) == 1 and col.name == "Primitives" \
                else f"{col.name}.{slugify(mode)}.tokens.json"
            files[name] = json.dumps(_nest([(v.path, _leaf(v, mode)) for v in col.variables]),
                                     indent=2, ensure_ascii=False) + "\n"
    return files


def style_dictionary_config(collections, cap=256):
    """One CSS file per combination of modes, merging primitives with one mode of every collection."""
    import itertools
    multi = [c for c in collections if c.name != "Primitives"]
    combos = []
    for picks in itertools.product(*[c.modes for c in multi]):
        src = ["tokens/Primitives.tokens.json"] + [f"tokens/{c.name}.{slugify(m)}.tokens.json"
                                                    for c, m in zip(multi, picks)]
        name = "-".join(slugify(m) for c, m in zip(multi, picks) if len(c.modes) > 1) or "tokens"
        combos.append({"name": name, "source": src})
    truncated = len(combos) > cap
    combos = combos[:cap]
    note = f"// First {cap} combinations only; trim or extend this array as needed.\n" if truncated else ""
    return ("// Run: npm i style-dictionary && node sd.config.mjs   (token files in ./tokens)\n" + note +
            "import StyleDictionary from 'style-dictionary';\n"
            f"const combos = {json.dumps(combos, indent=2)};\n"
            "for (const c of combos) {\n"
            "  const sd = new StyleDictionary({\n"
            "    source: c.source,\n"
            "    platforms: { css: { transformGroup: 'css', buildPath: 'css/',\n"
            "      files: [{ destination: `${c.name}.css`, format: 'css/variables' }] } },\n"
            "  });\n"
            "  await sd.buildAllPlatforms();\n"
            "}\n")
