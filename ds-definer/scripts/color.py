"""Color math: hex <-> OKLCH (gamut-clamped) and WCAG 2.x contrast. Stdlib only."""
import math


def normalize_hex(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"invalid hex color: {h!r}")
    return "#" + h.upper()


def hex_to_rgb(h):
    h = normalize_hex(h)[1:]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return "#%02X%02X%02X" % (r, g, b)


def _to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_linear(h):
    return tuple(_to_linear(v / 255) for v in hex_to_rgb(h))


def hex_to_srgb_floats(h):
    return tuple(v / 255 for v in hex_to_rgb(h))


def hex_to_oklch(h):
    r, g, b = hex_to_linear(h)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.hypot(a, bb)
    hue = math.degrees(math.atan2(bb, a)) % 360 if C > 1e-4 else 0.0
    return L, (C if C > 1e-4 else 0.0), hue


def _oklch_to_linear(L, C, hue):
    a = C * math.cos(math.radians(hue))
    b = C * math.sin(math.radians(hue))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def _in_gamut(rgb, eps=1e-6):
    return all(-eps <= c <= 1 + eps for c in rgb)


def oklch_to_hex(L, C, hue):
    """Convert to hex; if out of sRGB gamut, reduce chroma (keeping L and hue)."""
    L = max(0.0, min(1.0, L))
    rgb = _oklch_to_linear(L, C, hue)
    if not _in_gamut(rgb):
        lo, hi = 0.0, C
        for _ in range(40):
            mid = (lo + hi) / 2
            if _in_gamut(_oklch_to_linear(L, mid, hue)):
                lo = mid
            else:
                hi = mid
        rgb = _oklch_to_linear(L, lo, hue)
    return rgb_to_hex(*(round(_from_linear(c) * 255) for c in rgb))


def relative_luminance(h):
    r, g, b = hex_to_linear(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(h1, h2):
    a, b = relative_luminance(h1), relative_luminance(h2)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)
