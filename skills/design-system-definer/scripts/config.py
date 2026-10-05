"""Config loading: skill defaults < preset < project config (later wins)."""
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
import yaml  # noqa: E402  (vendored PyYAML, pure Python)

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"
CONTRAST_LEVELS = {"AA": {"text": 4.5, "ui": 3.0}, "AAA": {"text": 7.0, "ui": 4.5}}
SUPPORTED_DIMENSIONS = ("brand", "theme", "device", "platform", "density", "a11y", "context", "locale")
STATUS_ROLES = {"error": "red", "success": "green", "warning": "amber", "info": "blue"}

DEFAULT_STYLES = [
    # name, size token, family role, weight role
    ["Heading/Display", "display", "heading", "heading"],
    ["Heading/XL", "heading-xl", "heading", "heading"],
    ["Heading/L", "heading-l", "heading", "heading"],
    ["Heading/M", "heading-m", "heading", "heading"],
    ["Body/L", "body-l", "body", "body"],
    ["Body/M", "body-m", "body", "body"],
    ["Body/S", "body-s", "body", "body"],
    ["Body/Caption", "caption", "body", "body"],
    ["Label/M", "body-m", "body", "heading"],
    ["Label/S", "body-s", "body", "heading"],
]

DEFAULTS = {
    "preset": None,
    "system_type": "custom",
    "base_mode": "ask",
    "dimensions": [],
    "brands": [],
    "base": {},
    "color": {
        "space": "oklch",
        "steps": [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
        "contrast": "AA",
        "neutrals": {"cool": "#64748B", "warm": "#78716C"},
        "status": {"red": "#DC2626", "green": "#16A34A", "amber": "#D97706", "blue": "#2563EB"},
    },
    "spacing": {"base": 4, "scale": [0, 0.5, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16]},
    "radius": {"scale": [0, 4, 8, 12, 16, 24], "full": 9999},
    "border": {"scale": [1, 2, 3]},
    "size": {"scale": [16, 20, 24, 32, 40, 44, 48, 56]},
    "type": {
        "scale": [12, 14, 16, 18, 20, 24, 28, 32, 40, 48, 56],
        "line_heights": [16, 20, 24, 28, 32, 36, 40, 48, 56, 64],
        "weights": [400, 500, 600, 700, 800, 900],
        "styles": DEFAULT_STYLES,
    },
    "device": {
        "modes": ["Mobile", "Desktop"],
        "space": {"xs": [4, 4], "sm": [8, 8], "md": [16, 20], "lg": [24, 32],
                  "xl": [32, 48], "2xl": [48, 64]},
        "type": {
            "display": {"size": [32, 48], "line": [40, 56]},
            "heading-xl": {"size": [28, 40], "line": [36, 48]},
            "heading-l": {"size": [24, 32], "line": [32, 40]},
            "heading-m": {"size": [20, 24], "line": [28, 32]},
            "body-l": {"size": [18, 18], "line": [28, 28]},
            "body-m": {"size": [16, 16], "line": [24, 24]},
            "body-s": {"size": [14, 14], "line": [20, 20]},
            "caption": {"size": [12, 12], "line": [16, 16]},
        },
        "margin": [16, 40],
        "control": [48, 48],
        "icon": [20, 20],
    },
    "motion": {"duration": {"short": 150, "medium": 250, "long": 400}},
    "platform": {
        "modes": ["Web", "iOS", "Android"],
        "control": [44, 44, 48],  # touch targets: Apple HIG 44pt, Material 48dp
        "icon": [20, 24, 24],
        "duration": {"short": [150, 200, 100], "medium": [250, 350, 250], "long": [400, 500, 300]},
    },
    "density": {
        "modes": ["Compact", "Comfortable", "Spacious"],
        "inset": [8, 12, 16], "stack": [8, 16, 24], "section": [24, 32, 48],
    },
    "a11y": {"large_text_scale": 1.25, "large_focus_width": 3},
    "context": {
        "marketing_type": {
            "display-xl": {"size": [40, 72], "line": [48, 80]},
            "display-l": {"size": [32, 56], "line": [40, 64]},
        },
    },
    "locale": {
        "modes": ["Latin", "Japanese", "Arabic"],
        "families": {"Japanese": "Noto Sans JP", "Arabic": "Noto Sans Arabic"},
        "direction": {"Arabic": "rtl"},
    },
    "custom_dimensions": [],
    "tiers": {"component_tokens": "minimal"},
    "components": ["button", "text-field", "checkbox", "radio", "selectable-card",
                  "progress", "feedback"],
    "outputs": ["figma", "dtcg", "decision-records", "build-plan"],
}

BRAND_DEFAULTS = {
    "fonts": {"heading": "Inter", "body": None},
    "weights": {"heading": 600, "body": 400},
    "radius": {"button": 8, "field": 8, "card": 8, "control": 4},
    "border": {"default": 1, "focus": 2},
    "density": "default",
    "easing": [0.5, 0, 0.5, 1],
}


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower().replace("'", "").replace("’", ""))
    return s.strip("-")


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def resolve_contrast(value):
    if isinstance(value, str):
        if value.upper() not in CONTRAST_LEVELS:
            raise ValueError(f"contrast must be AA, AAA or {{text, ui}}; got {value!r}")
        return dict(CONTRAST_LEVELS[value.upper()])
    out = {"text": float(value["text"]), "ui": float(value["ui"])}
    if out["ui"] > out["text"]:
        raise ValueError("contrast.ui must not exceed contrast.text")
    return out


def resolve_extends(raws):
    """House of brands: a brand with `extends: <name>` inherits that brand's settings."""
    by_name = {str(r["name"]): r for r in raws}

    def resolve(r, seen=()):
        parent = r.get("extends")
        if not parent:
            return copy.deepcopy(r)
        if parent not in by_name:
            raise ValueError(f"brand {r['name']!r} extends unknown brand {parent!r}")
        if r["name"] in seen:
            raise ValueError(f"brand extends cycle at {r['name']!r}")
        merged = deep_merge(resolve(by_name[parent], seen + (r["name"],)), {k: v for k, v in r.items() if k != "extends"})
        merged["name"] = r["name"]
        if "slug" not in r:
            merged.pop("slug", None)
        return merged

    return [resolve(r) for r in raws]


def normalize_brand(raw, neutral_names):
    b = deep_merge(BRAND_DEFAULTS, raw)
    b["name"] = str(raw["name"])
    b["slug"] = raw.get("slug") or slugify(b["name"])
    b["anchors"] = {slugify(k): v for k, v in (raw.get("anchors") or {}).items()}
    primary = raw.get("primary")
    if primary is None:
        primary = next(iter(b["anchors"]), "neutral")
    b["primary"] = slugify(primary) if primary != "neutral" else "neutral"
    if b["primary"] != "neutral" and b["primary"] not in b["anchors"]:
        raise ValueError(f"brand {b['name']!r}: primary {primary!r} is not one of its anchors")
    b["neutral"] = raw.get("neutral") or neutral_names[0]
    if b["neutral"] not in neutral_names:
        raise ValueError(f"brand {b['name']!r}: neutral {b['neutral']!r} not in {neutral_names}")
    if not b["fonts"].get("body"):
        b["fonts"]["body"] = b["fonts"]["heading"]
    if b["density"] not in ("default", "roomy"):
        raise ValueError(f"brand {b['name']!r}: density must be default or roomy")
    if len(b["easing"]) != 4:
        raise ValueError(f"brand {b['name']!r}: easing needs 4 numbers")
    for role, v in b["radius"].items():
        if v != "full" and not isinstance(v, (int, float)):
            raise ValueError(f"brand {b['name']!r}: radius.{role} must be a number or 'full'")
    return b


def load_config(path):
    text = Path(path).read_text(encoding="utf-8")
    user = yaml.safe_load(text) or {}
    cfg = copy.deepcopy(DEFAULTS)
    preset = user.get("preset")
    if preset:
        pfile = PRESET_DIR / f"{preset}.yaml"
        if not pfile.exists():
            raise ValueError(f"unknown preset {preset!r}; available: "
                             f"{sorted(p.stem for p in PRESET_DIR.glob('*.yaml'))}")
        cfg = deep_merge(cfg, yaml.safe_load(pfile.read_text(encoding="utf-8")) or {})
    cfg = deep_merge(cfg, user)
    cfg["_source_text"] = text
    cfg["color"]["contrast"] = resolve_contrast(cfg["color"]["contrast"])
    neutral_names = list(cfg["color"]["neutrals"])

    if not cfg["brands"]:
        raise ValueError("config needs at least one brand")
    cfg["brands"] = resolve_extends(cfg["brands"])
    brands = [normalize_brand(b, neutral_names) for b in cfg["brands"]]
    cfg["brands"] = brands

    custom = cfg["custom_dimensions"] or []
    custom_names = [c["name"] for c in custom]
    dims = list(cfg["dimensions"]) or (["brand"] if len(brands) > 1 else [])
    bad = [d for d in dims if d not in SUPPORTED_DIMENSIONS]
    if bad:
        raise ValueError(f"dimension(s) {bad} are not built in; built-in: {list(SUPPORTED_DIMENSIONS)}. "
                         "For anything else define it under custom_dimensions (see references/config-reference.md)")
    if len(set(dims)) != len(dims):
        raise ValueError("dimensions contains duplicates")
    if len(brands) > 1 and "brand" not in dims:
        raise ValueError("more than one brand requires the 'brand' dimension")
    for c in custom:
        if not c.get("modes") or not c.get("tokens"):
            raise ValueError(f"custom dimension {c.get('name')!r} needs modes and tokens")
    if len(set(custom_names)) != len(custom_names) or set(custom_names) & set(
            ["Primitives", "Brand", "Theme", "Device", "Platform", "Density", "A11y", "Locale"]):
        raise ValueError("custom dimension names must be unique and not reuse a built-in collection name")
    cfg["dimensions"] = dims

    modes_brands = list(brands)
    if "brand" in dims:
        if cfg["base_mode"] == "ask":
            raise ValueError("base_mode is 'ask': decide include or none (the interview asks "
                             "this once) and set it in the config")
        if cfg["base_mode"] not in ("include", "none"):
            raise ValueError("base_mode must be include, none or ask")
        if cfg["base_mode"] == "include":
            base = normalize_brand({"name": "Base", "slug": "base", "anchors": {},
                                    **(cfg.get("base") or {})}, neutral_names)
            modes_brands = [base] + brands
    cfg["mode_brands"] = modes_brands

    dev = cfg["device"]
    n = len(dev["modes"])
    flat = [dev["margin"], dev["control"], dev["icon"], *dev["space"].values()]
    flat += [t["size"] for t in dev["type"].values()] + [t["line"] for t in dev["type"].values()]
    flat += [t["size"] for t in cfg["context"]["marketing_type"].values()]
    flat += [t["line"] for t in cfg["context"]["marketing_type"].values()]
    if any(len(x) != n for x in flat):
        raise ValueError(f"every device value needs {n} entries (one per device mode)")
    plat = cfg["platform"]
    pn = len(plat["modes"])
    if any(len(x) != pn for x in [plat["control"], plat["icon"], *plat["duration"].values()]):
        raise ValueError(f"every platform value needs {pn} entries (one per platform mode)")
    den = cfg["density"]
    dn = len(den["modes"])
    if any(len(den[k]) != dn for k in ("inset", "stack", "section")):
        raise ValueError(f"every density value needs {dn} entries (one per density mode)")
    if "context" in dims:
        have = {st[0] for st in cfg["type"]["styles"]}
        for k in cfg["context"]["marketing_type"]:
            words = " ".join(w.upper() if len(w) <= 2 else w.capitalize() for w in k.split("-"))
            name = "Marketing/" + words
            if name not in have:
                cfg["type"]["styles"].append([name, f"marketing-{k}", "heading", "heading"])
    if cfg["tiers"]["component_tokens"] not in ("none", "minimal", "full"):
        raise ValueError("tiers.component_tokens must be none, minimal or full")
    return cfg
