"""Contrast matrix: check pairs against targets, suggest fixes, render reports."""
import csv
import io
from dataclasses import dataclass

from color import contrast_ratio, hex_to_oklch, oklch_to_hex


@dataclass
class PairResult:
    id: str
    mode: str
    kind: str  # "text" | "ui"
    fg: str
    bg: str
    required: float
    ratio: float
    passed: bool
    fix: str = ""  # suggested replacement for fg when failing


def suggest_fix(fg, bg, required):
    """Nudge fg lightness (keeping hue and chroma) until it meets `required` on bg."""
    L, C, h = hex_to_oklch(fg)
    bg_is_light = hex_to_oklch(bg)[0] > 0.5
    step = -0.005 if bg_is_light else 0.005
    for _ in range(200):
        L += step
        candidate = oklch_to_hex(L, C, h)
        if contrast_ratio(candidate, bg) >= required:
            return candidate
        if not 0.0 < L < 1.0:
            break
    extreme = "#000000" if bg_is_light else "#FFFFFF"
    return extreme if contrast_ratio(extreme, bg) >= required else ""  # "" = change the background


def check_pair(pair_id, mode, kind, fg, bg, targets):
    required = targets[kind]
    ratio = contrast_ratio(fg, bg)
    passed = ratio >= required
    return PairResult(pair_id, mode, kind, fg, bg, required, ratio, passed,
                      "" if passed else suggest_fix(fg, bg, required))


def to_markdown(results, notes=()):
    failing = [r for r in results if not r.passed]
    lines = ["# Contrast matrix", "",
             f"{len(results)} pairs checked, {len(failing)} failing.", ""]
    lines += ["| Pair | Mode | Kind | Foreground | Background | Ratio | Required | Result | Suggested fix |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r.id} | {r.mode} | {r.kind} | {r.fg} | {r.bg} | {r.ratio:.2f} | "
                     f"{r.required:g} | {'pass' if r.passed else 'FAIL'} | {r.fix} |")
    if notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"


def to_csv(results):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["pair", "mode", "kind", "foreground", "background", "ratio", "required", "result", "suggested_fix"])
    for r in results:
        w.writerow([r.id, r.mode, r.kind, r.fg, r.bg, f"{r.ratio:.2f}", f"{r.required:g}",
                    "pass" if r.passed else "fail", r.fix])
    return buf.getvalue()
