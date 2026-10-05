"""Config loading: skill defaults < preset < project config (later wins)."""
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
import yaml  # noqa: E402  (vendored PyYAML, pure Python)

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"
CONTRAST_LEVELS = {"AA": {"text": 4.5, "ui": 3.0}, "AAA": {"text": 7.0, "ui": 4.5}}
SUPPORTED_DIMENSIONS = ("brand", "theme", "device")
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
    brands = [normalize_brand(b, neutral_names) for b in cfg["brands"]]
    cfg["brands"] = brands

    dims = list(cfg["dimensions"]) or (["brand"] if len(brands) > 1 else [])
    bad = [d for d in dims if d not in SUPPORTED_DIMENSIONS]
    if bad:
        raise ValueError(f"dimension(s) {bad} are not supported in v1; supported: "
                         f"{list(SUPPORTED_DIMENSIONS)}. See references/system-types.md")
    if "brand" in dims and "theme" in dims:
        raise ValueError("brand and theme together are not supported in v1 (would need "
                         "brand x theme mode combinations); choose one, or model dark mode "
                         "as separate systems")
    if len(brands) > 1 and "brand" not in dims:
        raise ValueError("more than one brand requires the 'brand' dimension")
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
    if any(len(x) != n for x in flat):
        raise ValueError(f"every device value needs {n} entries (one per device mode)")
    if cfg["tiers"]["component_tokens"] not in ("none", "minimal", "full"):
        raise ValueError("tiers.component_tokens must be none, minimal or full")
    return cfg
