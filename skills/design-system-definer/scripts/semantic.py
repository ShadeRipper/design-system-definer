"""Semantic and device tiers, derived from the primitives by contrast-aware rules.

Every semantic color/number/string is an alias; only easing is a literal. The rules
(not hand-picked steps) choose which ramp step each role points at, so a different
anchor or contrast target re-derives a passing system.
"""
from color import contrast_ratio
from config import STATUS_ROLES, slugify
from contrast import check_pair
from model import Alias, Collection, Variable
from primitives import num, radius_key

PRIM = "Primitives"
DEVICE = "Device"

COLOR_META = {
    "color/action/primary/default": (["FRAME_FILL", "SHAPE_FILL"], "Fill of primary actions (buttons, pills)"),
    "color/action/primary/hover": (["FRAME_FILL", "SHAPE_FILL"], "Primary action fill on hover"),
    "color/action/primary/pressed": (["FRAME_FILL", "SHAPE_FILL"], "Primary action fill while pressed"),
    "color/action/primary/border": (["FRAME_FILL", "SHAPE_FILL", "STROKE_COLOR"], "Outline of primary actions; carries the 3:1 edge when the fill alone does not"),
    "color/action/on-primary": (["SHAPE_FILL", "TEXT_FILL", "STROKE_COLOR"], "Text and icons on primary action fills"),
    "color/action/secondary/hover": (["FRAME_FILL", "SHAPE_FILL"], "Secondary action fill on hover"),
    "color/action/secondary/pressed": (["FRAME_FILL", "SHAPE_FILL"], "Secondary action fill while pressed"),
    "color/surface/brand": (["FRAME_FILL", "SHAPE_FILL"], "Brand-colored surface (hero, banner); pair with color/text/on-brand"),
    "color/surface/page": (["FRAME_FILL", "SHAPE_FILL", "EFFECT_COLOR"], "Page background"),
    "color/surface/card": (["FRAME_FILL", "SHAPE_FILL"], "Cards, fields and containers"),
    "color/surface/disabled": (["FRAME_FILL", "SHAPE_FILL"], "Disabled controls and fields"),
    "color/surface/error": (["FRAME_FILL", "SHAPE_FILL"], "Error message background"),
    "color/surface/success": (["FRAME_FILL", "SHAPE_FILL"], "Success message background"),
    "color/surface/warning": (["FRAME_FILL", "SHAPE_FILL"], "Warning message background"),
    "color/surface/info": (["FRAME_FILL", "SHAPE_FILL"], "Info message background"),
    "color/surface/track": (["FRAME_FILL", "SHAPE_FILL"], "Unfilled track of progress and switch controls"),
    "color/text/primary": (["TEXT_FILL", "STROKE_COLOR"], "Headings and body text"),
    "color/text/secondary": (["TEXT_FILL", "STROKE_COLOR"], "Helper text and labels"),
    "color/text/disabled": (["TEXT_FILL", "STROKE_COLOR"], "Disabled text; exempt from contrast requirements"),
    "color/text/error": (["TEXT_FILL", "STROKE_COLOR"], "Error text"),
    "color/text/success": (["TEXT_FILL", "STROKE_COLOR"], "Success text"),
    "color/text/warning": (["TEXT_FILL", "STROKE_COLOR"], "Warning text"),
    "color/text/info": (["TEXT_FILL", "STROKE_COLOR"], "Info text"),
    "color/text/on-brand": (["SHAPE_FILL", "TEXT_FILL", "STROKE_COLOR"], "Text on color/surface/brand"),
    "color/border/default": (["STROKE_COLOR"], "Field and control borders (3:1 non-text contrast)"),
    "color/border/strong": (["STROKE_COLOR"], "Emphasized borders"),
    "color/border/subtle": (["STROKE_COLOR"], "Decorative dividers; exempt from contrast requirements"),
    "color/border/error": (["STROKE_COLOR"], "Error state border"),
    "color/border/success": (["STROKE_COLOR"], "Success state border"),
    "color/border/warning": (["STROKE_COLOR"], "Warning state border"),
    "color/border/info": (["STROKE_COLOR"], "Info state border"),
    "color/indicator": (["SHAPE_FILL", "TEXT_FILL", "STROKE_COLOR", "EFFECT_COLOR"], "Focus rings, selection marks, progress fills; always meets 3:1 on page and card (the indicator vs action split)"),
    "color/on-indicator": (["SHAPE_FILL", "TEXT_FILL", "STROKE_COLOR"], "Marks drawn on color/indicator (checkmark on a checked box)"),
}
NUM_META = {
    "radius/button": (["CORNER_RADIUS"], "Corner radius of buttons"),
    "radius/field": (["CORNER_RADIUS"], "Corner radius of text fields"),
    "radius/card": (["CORNER_RADIUS"], "Corner radius of cards"),
    "radius/control": (["CORNER_RADIUS"], "Corner radius of small controls (checkbox box)"),
    "radius/round": (["CORNER_RADIUS"], "Fully rounded shapes: radio buttons, progress segments, pills"),
    "border-width/default": (["STROKE_FLOAT"], "Default stroke width"),
    "border-width/focus": (["STROKE_FLOAT"], "Focus ring stroke width"),
    "space/section": (["GAP"], "Gap between page sections"),
    "space/stack": (["GAP"], "Gap between stacked items"),
    "type/weight/heading": (["FONT_WEIGHT"], "Heading font weight"),
    "type/weight/body": (["FONT_WEIGHT"], "Body font weight"),
    "type/family/heading": (["FONT_FAMILY"], "Heading font family"),
    "type/family/body": (["FONT_FAMILY"], "Body font family"),
    "easing/standard": (["ALL_SCOPES"], "Standard motion easing curve"),
    "component/button/height": (["WIDTH_HEIGHT"], "Button height"),
    "component/field/height": (["WIDTH_HEIGHT"], "Text field height"),
    "component/checkbox/size": (["WIDTH_HEIGHT"], "Checkbox and radio box size"),
    "component/progress/height": (["WIDTH_HEIGHT"], "Progress track height"),
}


# ---------------------------------------------------------------- device tier
def device_table(cfg):
    """[(path, per-mode px list, primitive prefix, scopes, description)]"""
    dev, tier = cfg["device"], cfg["tiers"]["component_tokens"]
    rows = [(f"space/{k}", v, "space", ["GAP"], f"Spacing step {k}") for k, v in dev["space"].items()]
    rows.append(("layout/margin", dev["margin"], "space", ["GAP", "WIDTH_HEIGHT"], "Page side margin"))
    rows += [(f"type/size/{k}", t["size"], "font/size", ["FONT_SIZE"], f"Font size: {k}")
             for k, t in dev["type"].items()]
    rows += [(f"type/line-height/{k}", t["line"], "font/line-height", ["LINE_HEIGHT"], f"Line height: {k}")
             for k, t in dev["type"].items()]
    if tier != "none":
        rows.append(("size/control", dev["control"], "size", ["WIDTH_HEIGHT"], "Height of interactive controls"))
        rows.append(("size/icon", dev["icon"], "size", ["WIDTH_HEIGHT"], "Icon size"))
    return rows


def build_device(cfg):
    dev = cfg["device"]
    col = Collection(DEVICE, list(dev["modes"]))
    for path, vals, prefix, scopes, desc in device_table(cfg):
        col.variables.append(Variable(path, "number", {
            m: Alias(f"{prefix}/{num(v)}", PRIM) for m, v in zip(dev["modes"], vals)}, scopes, desc))
    return col


# ---------------------------------------------------------------- color rules
class Deriver:
    def __init__(self, prims, cfg):
        self.P = prims.values
        self.ramps = prims.ramps
        self.steps = cfg["color"]["steps"]
        self.ui = cfg["color"]["contrast"]["ui"]
        self.text = cfg["color"]["contrast"]["text"]
        self.notes = []

    def c(self, a, b):
        return contrast_ratio(self.P[a], self.P[b])

    def step_of(self, path):
        return int(path.rsplit("/", 1)[1])

    def shift(self, prefix, step, k):
        i = max(0, min(len(self.steps) - 1, self.steps.index(step) + k))
        return f"{prefix}/{self.steps[i]}"

    def search(self, prefix, start, direction, ok):
        """First step from `start` toward darker (+1) or lighter (-1) that satisfies ok."""
        i = self.steps.index(start)
        seq = self.steps[i:] if direction > 0 else self.steps[:i + 1][::-1]
        for s in seq:
            if ok(f"{prefix}/{s}"):
                return f"{prefix}/{s}"
        return f"{prefix}/{seq[-1]}"  # best effort; the contrast matrix will flag it

    def pick_on(self, candidates, bg):
        for cand in candidates:
            if self.c(cand, bg) >= self.text:
                return cand
        return max(candidates, key=lambda cand: self.c(cand, bg))

    def colors(self, b, kind):
        dark = kind == "dark"
        N = f"color/neutral-{b['neutral']}"
        n = lambda s: f"{N}/{s}"  # noqa: E731
        ui, text = self.ui, self.text
        o = {}
        if not dark:
            page, card, disabled, track = n(50), "color/white", n(100), n(200)
            o["color/text/primary"], o["color/text/disabled"] = n(900), n(500)
            o["color/border/strong"], o["color/border/subtle"] = n(900), n(200)
            o["color/action/secondary/hover"], o["color/action/secondary/pressed"] = n(50), n(100)
            on_candidates = ["color/white", n(950), "color/black"]
            d = 1
        else:
            page, card, disabled, track = n(950), n(900), n(800), n(700)
            o["color/text/primary"], o["color/text/disabled"] = n(50), n(600)
            o["color/border/strong"], o["color/border/subtle"] = n(100), n(800)
            o["color/action/secondary/hover"], o["color/action/secondary/pressed"] = n(900), n(800)
            on_candidates = [n(950), "color/white", "color/black"]
            d = -1
        o["color/surface/page"], o["color/surface/card"] = page, card
        o["color/surface/disabled"], o["color/surface/track"] = disabled, track
        both = lambda p, t: all(self.c(p, bg) >= t for bg in (page, card))  # noqa: E731
        o["color/text/secondary"] = self.search(N, 600 if not dark else 400, d, lambda p: both(p, text))
        o["color/border/default"] = self.search(N, 400 if not dark else 600, d, lambda p: both(p, ui))

        for role, hue in STATUS_ROLES.items():
            hp = f"color/{hue}"
            surf = f"{hp}/{50 if not dark else 950}"
            o[f"color/surface/{role}"] = surf
            o[f"color/text/{role}"] = self.search(
                hp, 600 if not dark else 400, d,
                lambda p, surf=surf: self.c(p, card) >= text and self.c(p, surf) >= text)
            o[f"color/border/{role}"] = self.search(hp, 500, d, lambda p: self.c(p, card) >= ui)

        # Primary action and indicator.
        def fill_ok(p):
            return any(self.c(cand, p) >= text for cand in on_candidates[:2])

        if b["primary"] == "neutral":
            fp, fill_step = N, (900 if not dark else 100)
            fill = n(fill_step)
        else:
            fp = f"color/{b['slug']}/{b['primary']}"
            ramp = self.ramps[fp]
            start = ramp.anchor_step if ramp.anchor_on_ramp else 600
            ok = (lambda p: fill_ok(p)) if not dark else (lambda p: fill_ok(p) and self.c(p, page) >= ui)
            fill = self.search(fp, start, d, ok)
            fill_step = self.step_of(fill)
            if fill_step != start and ramp.anchor_on_ramp:
                self.notes.append(f"{b['name']} ({kind}): action fill moved from step {start} to "
                                  f"{fill_step} so text on it meets {text:g}:1")
        o["color/action/primary/default"] = fill
        on_primary = self.pick_on(on_candidates, fill)

        def states():
            """Hover and pressed: step away from the fill, but only to steps text still reads on."""
            found = []
            for direction in (d, -d):
                for k in (1, 2):
                    cand = self.shift(fp, fill_step, direction * k)
                    if cand != fill and cand not in found and self.c(on_primary, cand) >= text:
                        found.append(cand)
                    elif cand == fill or self.c(on_primary, cand) < text:
                        break
                if len(found) >= 2:
                    break
            return (found + [fill, fill])[:2]

        o["color/action/primary/hover"], o["color/action/primary/pressed"] = states()
        if self.c(fill, page) >= ui:
            o["color/action/primary/border"] = fill
        else:
            o["color/action/primary/border"] = self.search(fp, fill_step, d, lambda p: self.c(p, page) >= ui)
        o["color/action/on-primary"] = on_primary
        o["color/surface/brand"] = fill
        o["color/text/on-brand"] = o["color/action/on-primary"]
        if b["primary"] == "neutral":
            ind = fill
        else:
            start_i = max(fill_step, 500) if not dark else fill_step
            ind = self.search(fp, start_i, d, lambda p: both(p, ui))
        o["color/indicator"] = ind
        o["color/on-indicator"] = self.pick_on(on_candidates, ind)
        return o


# ---------------------------------------------------------------- assembly
def _alias_for(path, prims):
    return Alias(path, PRIM)


def role_values(cfg, prims, b, kind, deriver, has_device):
    """Ordered {path: (type, value)} for one mode."""
    tier = cfg["tiers"]["component_tokens"]
    out = {}
    for path, target in deriver.colors(b, kind).items():
        out[path] = ("color", Alias(target, PRIM))
    order = list(COLOR_META)
    out = {p: out[p] for p in order}

    for role in ("button", "field", "card", "control"):
        if role == "control" and tier == "none":
            continue
        out[f"radius/{role}"] = ("number", Alias(f"radius/{radius_key(b['radius'][role], cfg)}", PRIM))
    if tier != "none":
        out["radius/round"] = ("number", Alias("radius/full", PRIM))
    out["border-width/default"] = ("number", Alias(f"border/{num(b['border']['default'])}", PRIM))
    out["border-width/focus"] = ("number", Alias(f"border/{num(b['border']['focus'])}", PRIM))

    dev = cfg["device"]
    section_key, stack_key = ("2xl", "lg") if b["density"] == "roomy" else ("xl", "md")
    if has_device:
        out["space/section"] = ("number", Alias(f"space/{section_key}", DEVICE))
        out["space/stack"] = ("number", Alias(f"space/{stack_key}", DEVICE))
    else:
        out["space/section"] = ("number", Alias(f"space/{num(dev['space'][section_key][0])}", PRIM))
        out["space/stack"] = ("number", Alias(f"space/{num(dev['space'][stack_key][0])}", PRIM))
    out["type/weight/heading"] = ("number", Alias(f"font/weight/{num(b['weights']['heading'])}", PRIM))
    out["type/weight/body"] = ("number", Alias(f"font/weight/{num(b['weights']['body'])}", PRIM))
    out["type/family/heading"] = ("string", Alias(f"font/family/{slugify(b['fonts']['heading'])}", PRIM))
    out["type/family/body"] = ("string", Alias(f"font/family/{slugify(b['fonts']['body'])}", PRIM))
    out["easing/standard"] = ("easing", list(b["easing"]))

    if not has_device:  # no device dimension: device-level tokens live in this collection
        for path, vals, prefix, _scopes, _desc in device_table(cfg):
            out[path] = ("number", Alias(f"{prefix}/{num(vals[0])}", PRIM))
    if tier == "full":
        src = DEVICE if has_device else PRIM
        ctrl = "size/control" if has_device else f"size/{num(dev['control'][0])}"
        icon = "size/icon" if has_device else f"size/{num(dev['icon'][0])}"
        out["component/button/height"] = ("number", Alias(ctrl, src))
        out["component/field/height"] = ("number", Alias(ctrl, src))
        out["component/checkbox/size"] = ("number", Alias(icon, src))
        sp = "space/xs" if has_device else f"space/{num(dev['space']['xs'][0])}"
        out["component/progress/height"] = ("number", Alias(sp, src))
    return out


def meta_for(path, cfg):
    if path in COLOR_META:
        return COLOR_META[path]
    if path in NUM_META:
        return NUM_META[path]
    for p, vals, _prefix, scopes, desc in device_table(cfg):
        if p == path:
            return scopes, desc
    raise KeyError(path)


def build_semantic(cfg, prims):
    """Return (collections, mode_info). collections = [Device?, Brand|Theme]."""
    dims = cfg["dimensions"]
    has_device = "device" in dims
    deriver = Deriver(prims, cfg)
    if "theme" in dims:
        name = "Theme"
        modes = [("Light", cfg["brands"][0], "light"), ("Dark", cfg["brands"][0], "dark")]
    else:
        name = "Brand"
        modes = [(b["name"], b, "light") for b in cfg["mode_brands"]]
    col = Collection(name, [m[0] for m in modes])
    per_mode = {m: role_values(cfg, prims, b, kind, deriver, has_device) for m, b, kind in modes}
    first = per_mode[modes[0][0]]
    for path, (vtype, _v) in first.items():
        scopes, desc = meta_for(path, cfg)
        col.variables.append(Variable(path, vtype, {m: per_mode[m][path][1] for m, _, _ in modes},
                                      scopes, desc))
    col.notes = deriver.notes
    cols = ([build_device(cfg)] if has_device else []) + [col]
    return cols


# ---------------------------------------------------------------- contrast matrix
def _resolve(prims, value):
    return prims.values[value.target]


TEXT_PAIRS = [
    ("color/text/primary", "color/surface/page"), ("color/text/primary", "color/surface/card"),
    ("color/text/secondary", "color/surface/page"), ("color/text/secondary", "color/surface/card"),
    ("color/action/on-primary", "color/action/primary/default"),
    ("color/action/on-primary", "color/action/primary/hover"),
    ("color/action/on-primary", "color/action/primary/pressed"),
    ("color/text/on-brand", "color/surface/brand"),
    ("color/on-indicator", "color/indicator"),
]
UI_PAIRS = [
    ("color/indicator", "color/surface/page"), ("color/indicator", "color/surface/card"),
    ("color/border/default", "color/surface/page"), ("color/border/default", "color/surface/card"),
    ("color/action/primary/border", "color/surface/page"),
]
EXEMPT = ["color/text/disabled", "color/border/subtle", "color/surface/track",
          "color/surface/disabled"]


def check_semantic(cfg, prims, color_collection):
    targets = cfg["color"]["contrast"]
    pairs = list(TEXT_PAIRS), list(UI_PAIRS)
    text_pairs, ui_pairs = pairs
    for role in STATUS_ROLES:
        text_pairs += [(f"color/text/{role}", "color/surface/card"),
                       (f"color/text/{role}", f"color/surface/{role}")]
        ui_pairs.append((f"color/border/{role}", "color/surface/card"))
    results = []
    for mode in color_collection.modes:
        for kind, plist in (("text", text_pairs), ("ui", ui_pairs)):
            for fg, bg in plist:
                f = _resolve(prims, color_collection.get(fg).values[mode])
                g = _resolve(prims, color_collection.get(bg).values[mode])
                results.append(check_pair(f"{fg} on {bg}", mode, kind, f, g, targets))
    notes = [f"exempt from contrast requirements (disabled or decorative): {', '.join(EXEMPT)}"]
    return results, notes
