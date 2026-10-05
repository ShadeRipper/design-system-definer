"""Config loading: skill defaults < preset < project config (later wins)."""
import copy
import re
from pathlib import Path

import yaml

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"
CONTRAST_LEVELS = {"AA": {"text": 4.5, "ui": 3.0}, "AAA": {"text": 7.0, "ui": 4.5}}

DEFAULTS = {
    "preset": None,
    "system_type": "custom",
    "base_mode": "ask",
    "dimensions": [],
    "brands": [],
    "color": {
        "space": "oklch",
        "steps": [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
        "contrast": "AA",
        "neutral": "#737373",
    },
    "spacing": {"base": 4, "scale": [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24]},
    "radius": {"none": 0, "sm": 2, "md": 4, "lg": 8, "xl": 12, "2xl": 16, "round": 9999},
    "type": {
        "scale": [12, 14, 16, 18, 20, 24, 28, 32, 40, 48],
        "weights": {"regular": 400, "medium": 500, "semibold": 600, "bold": 700},
    },
    "tiers": {"component_tokens": "minimal"},
    "outputs": ["figma", "dtcg"],
}


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "").replace("’", ""))
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


def load_config(path):
    user = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cfg = copy.deepcopy(DEFAULTS)
    preset = user.get("preset")
    if preset:
        pfile = PRESET_DIR / f"{preset}.yaml"
        if not pfile.exists():
            raise ValueError(f"unknown preset {preset!r}; available: "
                             f"{sorted(p.stem for p in PRESET_DIR.glob('*.yaml'))}")
        cfg = deep_merge(cfg, yaml.safe_load(pfile.read_text(encoding="utf-8")) or {})
    cfg = deep_merge(cfg, user)
    cfg["color"]["contrast"] = resolve_contrast(cfg["color"]["contrast"])
    if not cfg["brands"]:
        raise ValueError("config needs at least one brand with anchors")
    for b in cfg["brands"]:
        b["slug"] = slugify(b["name"])
        if not b.get("anchors"):
            raise ValueError(f"brand {b['name']!r} has no anchors")
    slugs = [b["slug"] for b in cfg["brands"]]
    if len(set(slugs)) != len(slugs):
        raise ValueError("brand names must be unique after slugging")
    return cfg
