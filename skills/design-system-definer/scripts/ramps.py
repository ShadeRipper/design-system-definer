"""OKLCH ramps calibrated to a contrast target against white.

Contrast wins over anchor fidelity (PRD R3):
  - step 500 meets the UI target, step 600 meets the text target, always.
  - the exact anchor hex is kept as its own primitive; it also replaces its
    nearest ramp step, but only if that step's requirement is still met.
"""
from dataclasses import dataclass, field

from color import contrast_ratio, hex_to_oklch, normalize_hex, oklch_to_hex

WHITE, BLACK = "#FFFFFF", "#000000"
L_LIGHT = 0.975  # lightness of the first step
L_DARK = 0.20  # lightness of the last step (lowered if the text target forces it)


@dataclass
class Ramp:
    steps: dict  # step -> hex
    lightness: dict  # step -> OKLCH L
    anchor: str
    anchor_step: int
    anchor_on_ramp: bool
    anchor_contrast_white: float
    anchor_contrast_black: float
    safe_text: str  # "white" or "black": the text color that works on the anchor
    notes: list = field(default_factory=list)


def _taper(L, l_dark, l_light):
    t = max(0.0, min(1.0, (L - l_dark) / (l_light - l_dark)))
    return 0.2 + 0.8 * 4 * t * (1 - t)


def _solve_lightness(target, hue, chroma, l_dark, l_light):
    """Largest L whose (gamut-clamped, hex-rounded) color reaches `target` on white."""

    def color(L):
        return oklch_to_hex(L, chroma * _taper(L, l_dark, l_light), hue)

    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if contrast_ratio(color(mid), WHITE) >= target:
            lo = mid
        else:
            hi = mid
    L = lo
    while contrast_ratio(color(L), WHITE) < target and L > 0:
        L -= 0.0005  # hex rounding can land a hair under the target
    return L


def required_ratio(step, ui, text):
    """Contrast a ramp step must reach against white (None = no requirement)."""
    if step == 500:
        return ui
    if step >= 600:
        return text
    return None


def generate_ramp(anchor_hex, steps, ui=3.0, text=4.5):
    anchor = normalize_hex(anchor_hex)
    steps = list(steps)
    if 500 not in steps or 600 not in steps:
        raise ValueError("steps must include 500 and 600 (the contrast-calibrated steps)")
    if ui > text:
        raise ValueError(f"ui contrast ({ui}) must not exceed text contrast ({text})")
    _, chroma, hue = hex_to_oklch(anchor)

    # Solve the lightness of the two pinned steps first, then interpolate the rest.
    l_dark = L_DARK
    l500 = _solve_lightness(ui, hue, chroma, l_dark, L_LIGHT)
    l600 = _solve_lightness(text, hue, chroma, l_dark, L_LIGHT)
    if l600 <= l_dark + 0.03:
        l_dark = max(0.04, l600 * 0.6)
    i500, i600, last = steps.index(500), steps.index(600), len(steps) - 1
    nodes = [(0, L_LIGHT), (i500, l500), (i600, l600), (last, l_dark)]

    def lightness_at(i):
        for (i0, v0), (i1, v1) in zip(nodes, nodes[1:]):
            if i0 <= i <= i1:
                return v0 + (v1 - v0) * ((i - i0) / (i1 - i0) if i1 != i0 else 0)

    lightness = {s: lightness_at(i) for i, s in enumerate(steps)}
    ramp_steps = {
        s: oklch_to_hex(L, chroma * _taper(L, l_dark, L_LIGHT), hue)
        for s, L in lightness.items()
    }

    # Anchor: nearest step by lightness; snap only if that step's requirement holds.
    anchor_l = hex_to_oklch(anchor)[0]
    nearest = min(steps, key=lambda s: abs(lightness[s] - anchor_l))
    c_white, c_black = contrast_ratio(anchor, WHITE), contrast_ratio(anchor, BLACK)
    need = required_ratio(nearest, ui, text)
    on_ramp = need is None or c_white >= need
    notes = []
    if on_ramp:
        ramp_steps[nearest] = anchor
    else:
        notes.append(
            f"anchor {anchor} is {c_white:.2f}:1 on white but step {nearest} needs "
            f"{need}:1; ramp calibrated instead, anchor kept as its own token"
        )
    safe = "black" if c_black > c_white else "white"
    if min(c_white, c_black) < ui:
        notes.append(f"pair the anchor with {safe} text ({max(c_white, c_black):.2f}:1)")
    return Ramp(ramp_steps, lightness, anchor, nearest, on_ramp, c_white, c_black, safe, notes)
