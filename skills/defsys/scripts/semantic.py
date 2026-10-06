"""Semantic and device tiers, derived from the primitives by contrast-aware rules.

Every semantic color/number/string is an alias; only easing is a literal. The rules
(not hand-picked steps) choose which ramp step each role points at, so a different
anchor or contrast target re-derives a passing system.
"""
from dataclasses import dataclass

from color import contrast_ratio
from config import slugify
from contrast import check_pair
from model import Alias, Collection, Variable
from primitives import prim_path, validate_path

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
    "color/surface/inverse": (["FRAME_FILL", "SHAPE_FILL"], "Dark surface on a light page (sidebar, footer band); pair with color/text/inverse"),
    "color/surface/brand-deep": (["FRAME_FILL", "SHAPE_FILL"], "Deep brand-colored section; pair with color/text/inverse"),
    "color/surface/brand-subtle": (["FRAME_FILL", "SHAPE_FILL"], "Pale brand tint for selected rows, highlights and tags; text/primary and text/brand read on it"),
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
    "color/text/inverse": (["SHAPE_FILL", "TEXT_FILL", "STROKE_COLOR"], "Text and icons on color/surface/inverse and color/surface/brand-deep"),
    "color/text/brand": (["TEXT_FILL", "STROKE_COLOR"], "Brand-colored text and links on page, card and brand-subtle"),
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
    "type/weight/ui": (["FONT_WEIGHT"], "Interface label font weight (navigation, buttons, list labels)"),
    "type/family/heading": (["FONT_FAMILY"], "Heading font family"),
    "type/family/body": (["FONT_FAMILY"], "Body font family"),
    "type/family/ui": (["FONT_FAMILY"], "Interface label font family (navigation, buttons, list labels)"),
    "easing/standard": (["ALL_SCOPES"], "Standard motion easing curve"),
    "component/button/height": (["WIDTH_HEIGHT"], "Button height"),
    "component/field/height": (["WIDTH_HEIGHT"], "Text field height"),
    "component/checkbox/size": (["WIDTH_HEIGHT"], "Checkbox and radio box size"),
    "component/progress/height": (["WIDTH_HEIGHT"], "Progress track height"),
}


# ---------------------------------------------------------------- color rules
class Deriver:
    def __init__(self, prims, cfg):
        self.cfg = cfg
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

        for role, hue in self.cfg["status_roles"].items():
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
        # Inverse and deep-brand surfaces, the brand tint, and brand-colored text.
        o["color/surface/inverse"] = n(950) if not dark else n(50)
        if b["primary"] == "neutral":
            o["color/surface/brand-deep"] = n(900) if not dark else n(100)
            o["color/surface/brand-subtle"] = n(100) if not dark else n(800)
        else:
            deep_start = 900 if not dark else 100
            o["color/surface/brand-deep"] = self.search(
                fp, deep_start, d, lambda p: any(self.c(c, p) >= text for c in on_candidates[:2]))
            o["color/surface/brand-subtle"] = f"{fp}/{50 if not dark else 950}"
        inv_bgs = [o["color/surface/inverse"], o["color/surface/brand-deep"]]
        o["color/text/inverse"] = next(
            (c for c in on_candidates if all(self.c(c, bg) >= text for bg in inv_bgs)),
            max(on_candidates, key=lambda c: min(self.c(c, bg) for bg in inv_bgs)))
        if b["primary"] == "neutral":
            o["color/text/brand"] = n(900) if not dark else n(100)
        else:
            o["color/text/brand"] = self.search(
                fp, 600 if not dark else 400, d,
                lambda p: all(self.c(p, bg) >= text for bg in (page, card, o["color/surface/brand-subtle"])))
        if b["primary"] == "neutral":
            ind = fill
        else:
            start_i = max(fill_step, 500) if not dark else fill_step
            ind = self.search(fp, start_i, d, lambda p: both(p, ui))
        o["color/indicator"] = ind
        o["color/on-indicator"] = self.pick_on(on_candidates, ind)
        return o



# ---------------------------------------------------------------- planning
DIM_COLLECTION = {"brand": "Brand", "theme": "Theme", "device": "Device", "platform": "Platform",
                  "density": "Density", "a11y": "A11y", "locale": "Locale"}
A11Y_MODES = ["Default", "Large text", "Reduced motion"]
DIM_WHY = {
    "brand": "brands differ independently of everything else, so each brand is a mode",
    "theme": "light and dark change the same roles with different values",
    "device": "spacing and type scale change with device, independent of brand or theme",
    "platform": "touch targets and motion follow platform conventions (Apple 44pt, Material 48dp)",
    "density": "compact, comfortable and spacious change spacing without changing the brand",
    "a11y": "large text and reduced motion override type, focus and motion tokens",
    "locale": "script and reading direction change the font family and layout direction",
}


def collection_name(cfg, dim):
    return DIM_COLLECTION.get(dim, dim)  # a custom dimension is its own name


def dim_modes(cfg, dim):
    dims = cfg["dimensions"]
    if dim == "brand":
        return [b["name"] for b in cfg["mode_brands"]] if "brand" in dims else [cfg["brands"][0]["name"]]
    return {"theme": ["Light", "Dark"], "device": cfg["device"]["modes"], "platform": cfg["platform"]["modes"],
            "density": cfg["density"]["modes"], "a11y": A11Y_MODES, "locale": cfg["locale"]["modes"]}[dim]


@dataclass
class Tok:
    path: str
    type: str
    dim: str
    values: dict  # mode -> spec
    scopes: list
    desc: str


class Planner:
    """Decides which collection owns each token and how override layers chain.

    A token that several active dimensions vary is built as a chain: the base layer
    holds absolute values; each override layer aliases the layer below (or overrides
    it). The top of the chain carries the canonical name components bind to; lower
    layers are prefixed with their dimension, so names never collide across files.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.dims = (set(cfg["dimensions"]) | {"brand"}) - {"context"}  # context adds tokens, no collection
        self.brands = cfg["mode_brands"]
        self.toks = []
        self.color_modes = []  # (label, brand, kind)

    def modes(self, dim):
        return dim_modes(self.cfg, dim)

    def add(self, dim, path, type_, values, scopes, desc):
        self.toks.append(Tok(path, type_, dim, values, scopes, desc))

    def chain(self, canon, type_, base_dim, base_values, scopes, desc, overrides=None):
        dims = [base_dim] + [d for d in (overrides or {}) if d in self.dims]
        prev = None
        for i, d in enumerate(dims):
            path = canon if i == len(dims) - 1 else f"{d}/{canon}"
            if i == 0:
                values = base_values
            else:
                values = {}
                for m in self.modes(d):
                    spec = overrides[d](m)
                    values[m] = spec if spec is not None else ("ref", prev[0], prev[1])
            note = "" if i == len(dims) - 1 else f" ({d} layer input; bind {canon})"
            self.add(d, path, type_, values, scopes, desc + note)
            prev = (path, d)
        return dims[-1]  # the dimension that holds the canonical token


def plan_tokens(cfg):
    P = Planner(cfg)
    dims, brands, tier = P.dims, P.brands, cfg["tiers"]["component_tokens"]
    dev, plat, den = cfg["device"], cfg["platform"], cfg["density"]
    a11y, loc, ctx = cfg["a11y"], cfg["locale"], cfg["context"]
    brand_active, theme_active = "brand" in cfg["dimensions"], "theme" in cfg["dimensions"]
    bmodes = P.modes("brand")

    # ---- color roles
    if theme_active and brand_active:
        for role, (scopes, desc) in COLOR_META.items():
            for variant in ("light", "dark"):
                P.add("brand", f"palette/{variant}/{role}", "color",
                      {b["name"]: ("color", role, b, variant) for b in brands}, scopes,
                      f"{desc} ({variant} palette input; bind {role})")
            P.add("theme", role, "color",
                  {"Light": ("ref", f"palette/light/{role}", "brand"),
                   "Dark": ("ref", f"palette/dark/{role}", "brand")}, scopes, desc)
        P.color_modes = [(f"{b['name']} / {t}", b, k) for b in brands
                         for t, k in (("Light", "light"), ("Dark", "dark"))]
    elif theme_active:
        b0 = brands[0]
        for role, (scopes, desc) in COLOR_META.items():
            P.add("theme", role, "color", {"Light": ("color", role, b0, "light"),
                                           "Dark": ("color", role, b0, "dark")}, scopes, desc)
        P.color_modes = [("Light", b0, "light"), ("Dark", b0, "dark")]
    else:
        for role, (scopes, desc) in COLOR_META.items():
            P.add("brand", role, "color", {b["name"]: ("color", role, b, "light") for b in brands}, scopes, desc)
        P.color_modes = [(b["name"], b, "light") for b in brands]

    # ---- shape, weights, easing (brand-owned)
    for role in ("button", "field", "card", "control"):
        if role == "control" and tier == "none":
            continue
        P.add("brand", f"radius/{role}", "number",
              {b["name"]: ("prim", "radius", b["radius"][role]) for b in brands}, *NUM_META[f"radius/{role}"])
    if tier != "none":
        P.add("brand", "radius/round", "number", {m: ("prim", "radius", "full") for m in bmodes},
              *NUM_META["radius/round"])
    P.add("brand", "border-width/default", "number",
          {b["name"]: ("prim", "border", b["border"]["default"]) for b in brands}, *NUM_META["border-width/default"])
    P.chain("border-width/focus", "number", "brand",
            {b["name"]: ("prim", "border", b["border"]["focus"]) for b in brands}, *NUM_META["border-width/focus"],
            overrides={"a11y": lambda m: ("prim", "border", a11y["large_focus_width"]) if m == "Large text" else None})
    for role in (("heading", "body", "ui") if cfg["ui_font"] else ("heading", "body")):
        P.add("brand", f"type/weight/{role}", "number",
              {b["name"]: ("prim", "weight", b["weights"][role]) for b in brands}, *NUM_META[f"type/weight/{role}"])
        P.chain(f"type/family/{role}", "string", "brand",
                {b["name"]: ("prim", "family", b["fonts"][role]) for b in brands}, *NUM_META[f"type/family/{role}"],
                overrides={"locale": lambda m: ("prim", "family", loc["families"][m]) if m in loc["families"] else None})
    P.add("brand", "easing/standard", "easing", {b["name"]: ("lit", list(b["easing"])) for b in brands},
          *NUM_META["easing/standard"])

    # ---- scale-like tokens: device is the base when active, else the brand collection
    scale_dim = "device" if "device" in dims else "brand"

    def base_values(dim, vals, kind):
        names = P.modes(dim)
        if dim == "brand":
            return {m: ("prim", kind, vals[0]) for m in names}
        return {m: ("prim", kind, v) for m, v in zip(names, vals)}

    for k, vals in dev["space"].items():
        P.chain(f"space/{k}", "number", scale_dim, base_values(scale_dim, vals, "space"), ["GAP"], f"Spacing step {k}")
    P.chain("layout/margin", "number", scale_dim, base_values(scale_dim, dev["margin"], "space"),
            ["GAP", "WIDTH_HEIGHT"], "Page side margin")

    # ---- rhythm: density owns it when active, else the brand layer (roomy brands use larger steps)
    if "density" in dims:
        for key in ("section", "stack", "inset"):
            P.add("density", f"space/{key}", "number",
                  {m: ("prim", "space", v) for m, v in zip(den["modes"], den[key])},
                  *(NUM_META.get(f"space/{key}") or (["GAP"], "Padding inside containers")))
    else:
        for key, (std, roomy) in (("section", ("xl", "2xl")), ("stack", ("md", "lg"))):
            base = {}
            for b in brands:
                k = roomy if b["density"] == "roomy" else std
                base[b["name"]] = (("ref", f"space/{k}", "device") if "device" in dims
                                   else ("prim", "space", dev["space"][k][0]))
            P.add("brand", f"space/{key}", "number", base, *NUM_META[f"space/{key}"])

    # ---- type scale, with a11y enlarging sizes that are the same in every lower mode
    def scaled(vals, kind):
        uniform = len(set(vals)) == 1
        return lambda m: (("prim", kind, round(vals[0] * a11y["large_text_scale"]))
                          if m == "Large text" and uniform else None)

    for k, t in dev["type"].items():
        P.chain(f"type/size/{k}", "number", scale_dim, base_values(scale_dim, t["size"], "font_size"),
                ["FONT_SIZE"], f"Font size: {k}", overrides={"a11y": scaled(t["size"], "font_size")})
        P.chain(f"type/line-height/{k}", "number", scale_dim, base_values(scale_dim, t["line"], "line"),
                ["LINE_HEIGHT"], f"Line height: {k}", overrides={"a11y": scaled(t["line"], "line")})
    if "context" in cfg["dimensions"]:
        for k, t in ctx["marketing_type"].items():
            P.chain(f"type/size/marketing-{k}", "number", scale_dim, base_values(scale_dim, t["size"], "font_size"),
                    ["FONT_SIZE"], f"Marketing font size: {k}")
            P.chain(f"type/line-height/marketing-{k}", "number", scale_dim,
                    base_values(scale_dim, t["line"], "line"), ["LINE_HEIGHT"], f"Marketing line height: {k}")

    # ---- control and icon size: platform, else device, else brand
    size_dim = "platform" if "platform" in dims else scale_dim
    size_vals = (plat["control"], plat["icon"]) if size_dim == "platform" else (dev["control"], dev["icon"])
    control_dim = icon_dim = None
    if tier != "none":
        control_dim = P.chain("size/control", "number", size_dim, base_values(size_dim, size_vals[0], "size"),
                              ["WIDTH_HEIGHT"], "Height of interactive controls")
        icon_dim = P.chain("size/icon", "number", size_dim, base_values(size_dim, size_vals[1], "size"),
                           ["WIDTH_HEIGHT"], "Icon size")

    # ---- motion durations: platform else brand base; reduced motion on top
    mot_dim = "platform" if "platform" in dims else "brand"
    for k in ("short", "medium", "long"):
        vals = plat["duration"][k] if mot_dim == "platform" else [cfg["motion"]["duration"][k]]
        P.chain(f"duration/{k}", "number", mot_dim, base_values(mot_dim, vals, "duration"), ["ALL_SCOPES"],
                f"Motion duration ({k}), ms",
                overrides={"a11y": lambda m: ("prim", "duration", 0) if m == "Reduced motion" else None})

    if "locale" in dims:
        P.add("locale", "layout/direction", "string",
              {m: ("lit", loc["direction"].get(m, "ltr")) for m in P.modes("locale")}, ["ALL_SCOPES"],
              "Reading direction (ltr or rtl)")

    if tier == "full":
        top = {"size/control": control_dim, "size/icon": icon_dim, "space/xs": scale_dim}
        for path, target in (("component/button/height", "size/control"), ("component/field/height", "size/control"),
                             ("component/checkbox/size", "size/icon"), ("component/progress/height", "space/xs")):
            P.add("brand", path, "number", {m: ("ref", target, top[target]) for m in bmodes}, *NUM_META[path])
    return P


def requirements(P):
    """Primitive values the plan needs, by kind."""
    need = {}
    for t in P.toks:
        for spec in t.values.values():
            if spec[0] == "prim":
                if spec[1] == "family":
                    need.setdefault("family", {})[slugify(spec[2])] = spec[2]
                else:
                    need.setdefault(spec[1], set()).add(spec[2])
    return need


# ---------------------------------------------------------------- assembly
def build_collections(cfg, prims, P):
    """Materialise the plan. Returns (collections in dependency order, derived color roles).

    derived maps a color-mode label to {role: primitive path}; the checks and the brief use it.
    """
    deriver = Deriver(prims, cfg)
    derived = {label: deriver.colors(b, kind) for label, b, kind in P.color_modes}
    cache = {}

    def roles(b, kind):
        key = (b["slug"], kind)
        if key not in cache:
            cache[key] = deriver.colors(b, kind)
        return cache[key]

    cols = {dim: Collection(collection_name(cfg, dim), list(P.modes(dim))) for dim in P.dims}

    def value(spec):
        kind = spec[0]
        if kind == "prim":
            return Alias(prim_path(spec[1], spec[2]), PRIM)
        if kind == "ref":
            return Alias(spec[1], collection_name(cfg, spec[2]))
        if kind == "lit":
            return spec[1]
        return Alias(roles(spec[2], spec[3])[spec[1]], PRIM)  # ("color", role, brand, kind)

    for t in P.toks:
        cols[t.dim].variables.append(Variable(t.path, t.type, {m: value(s) for m, s in t.values.items()},
                                              t.scopes, t.desc))
    out = [c for c in cols.values() if c.variables] + build_custom(cfg, prims)
    cols["brand"].notes = deriver.notes
    return order_by_dependency(out), derived


def build_custom(cfg, prims):
    """User-defined dimensions: tokens alias primitive paths (or are string/boolean literals)."""
    out = []
    for c in cfg["custom_dimensions"] or []:
        col = Collection(c["name"], list(c["modes"]))
        for path, spec in c["tokens"].items():
            validate_path(path)
            vtype = spec.get("type", "number")
            vals = spec["values"]
            if set(vals) != set(c["modes"]):
                raise ValueError(f"custom {c['name']}:{path} needs a value for each mode {c['modes']}")
            resolved = {}
            for m, v in vals.items():
                if vtype in ("string", "boolean") and not (isinstance(v, str) and v in prims.values):
                    resolved[m] = v
                else:
                    if v not in prims.values:
                        raise ValueError(f"custom {c['name']}:{path}:{m}: {v!r} is not a primitive; "
                                         "use a primitive path such as space/16 or color/white")
                    resolved[m] = Alias(v, PRIM)
            col.variables.append(Variable(path, vtype, resolved, spec.get("scopes", ["ALL_SCOPES"]),
                                          spec.get("description", f"{c['name']} token")))
        out.append(col)
    return out


def order_by_dependency(cols):
    """Primitives are not in `cols`; a collection comes after every collection it aliases."""
    byname = {c.name: c for c in cols}
    deps = {c.name: {v.collection for var in c.variables for v in var.values.values()
                     if isinstance(v, Alias) and v.collection not in (c.name, PRIM)} for c in cols}
    ordered, seen = [], set()

    def visit(name, stack=()):
        if name in seen:
            return
        if name in stack:
            raise ValueError(f"circular collection dependency at {name}")
        for d in sorted(deps.get(name, ())):
            if d in byname:
                visit(d, stack + (name,))
        seen.add(name)
        ordered.append(byname[name])

    for name in sorted(byname):
        visit(name)
    return ordered


# ---------------------------------------------------------------- contrast matrix
TEXT_PAIRS = [
    ("color/text/primary", "color/surface/page"), ("color/text/primary", "color/surface/card"),
    ("color/text/secondary", "color/surface/page"), ("color/text/secondary", "color/surface/card"),
    ("color/action/on-primary", "color/action/primary/default"),
    ("color/action/on-primary", "color/action/primary/hover"),
    ("color/action/on-primary", "color/action/primary/pressed"),
    ("color/text/on-brand", "color/surface/brand"),
    ("color/on-indicator", "color/indicator"),
    ("color/text/inverse", "color/surface/inverse"), ("color/text/inverse", "color/surface/brand-deep"),
    ("color/text/brand", "color/surface/page"), ("color/text/brand", "color/surface/card"),
    ("color/text/brand", "color/surface/brand-subtle"),
    ("color/text/primary", "color/surface/brand-subtle"),
]
UI_PAIRS = [
    ("color/indicator", "color/surface/page"), ("color/indicator", "color/surface/card"),
    ("color/border/default", "color/surface/page"), ("color/border/default", "color/surface/card"),
    ("color/action/primary/border", "color/surface/page"),
]
EXEMPT = ["color/text/disabled", "color/border/subtle", "color/surface/track",
          "color/surface/disabled"]


def check_semantic(cfg, prims, derived):
    targets = cfg["color"]["contrast"]
    text_pairs, ui_pairs = list(TEXT_PAIRS), list(UI_PAIRS)
    for role in cfg["status_roles"]:
        text_pairs += [(f"color/text/{role}", "color/surface/card"),
                       (f"color/text/{role}", f"color/surface/{role}")]
        ui_pairs.append((f"color/border/{role}", "color/surface/card"))
    results = []
    for label, roles in derived.items():
        for kind, plist in (("text", text_pairs), ("ui", ui_pairs)):
            for fg, bg in plist:
                results.append(check_pair(f"{fg} on {bg}", label, kind, prims.values[roles[fg]],
                                          prims.values[roles[bg]], targets))
    notes = [f"exempt from contrast requirements (disabled or decorative): {', '.join(EXEMPT)}"]
    return results, notes
