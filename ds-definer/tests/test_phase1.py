"""Phase 1 tests: R3 (ramps), R5 (contrast), R6 shape checks, R8 determinism.

Run from the repo root:  python -m unittest discover -s ds-definer/tests -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build import build  # noqa: E402
from color import contrast_ratio, hex_to_oklch, normalize_hex, oklch_to_hex  # noqa: E402
from config import load_config, resolve_contrast, slugify  # noqa: E402
from contrast import check_pair  # noqa: E402
from primitives import build_primitives, validate_path  # noqa: E402
from ramps import WHITE, generate_ramp  # noqa: E402

SAMPLE = ROOT / "examples" / "multi-brand-sample.yaml"
STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
LEVELS = {"AA": (3.0, 4.5), "AAA": (4.5, 7.0), "custom": (3.5, 5.5)}


class ColorMath(unittest.TestCase):
    def test_known_contrast(self):
        self.assertAlmostEqual(contrast_ratio("#000", "#FFF"), 21.0, places=2)
        self.assertAlmostEqual(contrast_ratio("#777777", "#FFFFFF"), 4.48, places=2)

    def test_hex_oklch_roundtrip(self):
        for h in ["#FFC72C", "#004B93", "#00704A", "#D52B1E", "#737373", "#000000", "#FFFFFF"]:
            self.assertEqual(oklch_to_hex(*hex_to_oklch(h)), h)

    def test_bad_hex(self):
        with self.assertRaises(ValueError):
            normalize_hex("#12")


class Ramps(unittest.TestCase):
    def assert_r3(self, anchor, ui, text):
        r = generate_ramp(anchor, STEPS, ui=ui, text=text)
        self.assertGreaterEqual(contrast_ratio(r.steps[500], WHITE), ui, anchor)
        self.assertGreaterEqual(contrast_ratio(r.steps[600], WHITE), text, anchor)
        for s in (700, 800, 900, 950):
            self.assertGreaterEqual(contrast_ratio(r.steps[s], WHITE), text, (anchor, s))
        lights = [hex_to_oklch(r.steps[s])[0] for s in STEPS]
        # lightness never increases down the ramp (small slack for anchor snap + rounding)
        for a, b in zip(lights, lights[1:]):
            self.assertLessEqual(b, a + 0.03, (anchor, lights))
        return r

    def test_r3_sample_brands_all_levels(self):
        for anchor in ["#FFC72C", "#D52B1E", "#004B93", "#E32934", "#00704A", "#737373"]:
            for ui, text in LEVELS.values():
                self.assert_r3(anchor, ui, text)

    def test_r3_hue_sweep(self):
        for hue in range(0, 360, 15):
            for L, C in [(0.9, 0.12), (0.7, 0.15), (0.5, 0.15), (0.3, 0.08)]:
                anchor = oklch_to_hex(L, C, hue)
                for ui, text in LEVELS.values():
                    self.assert_r3(anchor, ui, text)

    def test_contrast_wins_over_anchor(self):
        """Lay's yellow fails on white: it must not be forced onto a passing step."""
        r = generate_ramp("#FFC72C", STEPS, ui=3.0, text=4.5)
        self.assertEqual(r.anchor, "#FFC72C")
        self.assertLess(r.anchor_contrast_white, 3.0)
        self.assertEqual(r.safe_text, "black")
        self.assertGreaterEqual(r.anchor_contrast_black, 4.5)
        self.assertNotIn(r.anchor_step, (500, 600, 700, 800, 900, 950))
        self.assertEqual(r.steps[r.anchor_step], "#FFC72C")  # light step: exact anchor lands

    def test_anchor_lands_when_it_passes(self):
        r = generate_ramp("#D52B1E", STEPS, ui=3.0, text=4.5)
        self.assertTrue(r.anchor_on_ramp)
        self.assertEqual(r.steps[r.anchor_step], "#D52B1E")

    def test_anchor_flagged_when_nearest_step_cannot_pass(self):
        flagged = 0
        for hue in range(0, 360, 10):
            for L in (0.6, 0.65, 0.7, 0.75):
                anchor = oklch_to_hex(L, 0.15, hue)
                r = generate_ramp(anchor, STEPS, ui=4.5, text=7.0)
                if not r.anchor_on_ramp:
                    flagged += 1
                    self.assertEqual(r.anchor, normalize_hex(anchor))  # anchor itself untouched
                    self.assertTrue(any("anchor" in n for n in r.notes))
                self.assertGreaterEqual(contrast_ratio(r.steps[500], WHITE), 4.5)
                self.assertGreaterEqual(contrast_ratio(r.steps[600], WHITE), 7.0)
        self.assertGreater(flagged, 0)

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            generate_ramp("#FFC72C", [100, 200], ui=3, text=4.5)
        with self.assertRaises(ValueError):
            generate_ramp("#FFC72C", STEPS, ui=7, text=4.5)


class Contrast(unittest.TestCase):
    def test_failing_pair_gets_a_working_fix(self):
        r = check_pair("t", "m", "text", "#FFC72C", "#FFFFFF", {"text": 4.5, "ui": 3})
        self.assertFalse(r.passed)
        self.assertGreaterEqual(contrast_ratio(r.fix, "#FFFFFF"), 4.5)

    def test_dark_background_fix_goes_lighter(self):
        r = check_pair("t", "m", "text", "#333333", "#111111", {"text": 4.5, "ui": 3})
        self.assertFalse(r.passed)
        self.assertGreaterEqual(contrast_ratio(r.fix, "#111111"), 4.5)

    def test_no_fix_when_background_is_the_problem(self):
        r = check_pair("t", "m", "text", "#000000", "#E32934", {"text": 7.0, "ui": 4.5})
        self.assertFalse(r.passed)
        self.assertEqual(r.fix, "")

    def test_levels_and_custom(self):
        self.assertEqual(resolve_contrast("aaa"), {"text": 7.0, "ui": 4.5})
        self.assertEqual(resolve_contrast({"text": 5, "ui": 3.5}), {"text": 5.0, "ui": 3.5})
        with self.assertRaises(ValueError):
            resolve_contrast("AAAA")


class Pipeline(unittest.TestCase):
    def test_sample_builds_with_zero_failures(self):
        with tempfile.TemporaryDirectory() as d:
            results = build(SAMPLE, d)
            self.assertFalse([r for r in results if not r.passed])
            for rel in ["contrast-matrix.md", "contrast-matrix.csv",
                        "figma/Primitives.Value.tokens.json", "dtcg/tokens.json"]:
                self.assertTrue((Path(d) / rel).exists(), rel)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            build(SAMPLE, a)
            build(SAMPLE, b)
            for p in Path(a).rglob("*"):
                if p.is_file():
                    self.assertEqual(p.read_bytes(), (Path(b) / p.relative_to(a)).read_bytes())

    def test_changing_one_value_changes_output(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "c.yaml"
            cfg.write_text(SAMPLE.read_text(encoding="utf-8").replace("contrast: AA", "contrast: AAA"),
                           encoding="utf-8")
            build(SAMPLE, Path(d) / "aa")
            results = build(cfg, Path(d) / "aaa")
            self.assertFalse([r for r in results if not r.passed])
            self.assertNotEqual((Path(d) / "aa/dtcg/tokens.json").read_text(),
                                (Path(d) / "aaa/dtcg/tokens.json").read_text())

    def test_figma_colors_are_objects_not_plain_hex(self):
        with tempfile.TemporaryDirectory() as d:
            build(SAMPLE, d)
            data = json.loads((Path(d) / "figma/Primitives.Value.tokens.json").read_text("utf-8"))

        def walk(node):
            if "$type" in node:
                if node["$type"] == "color":
                    v = node["$value"]
                    self.assertIsInstance(v, dict)
                    self.assertEqual(set(v), {"colorSpace", "components", "alpha", "hex"})
                    self.assertEqual(len(v["components"]), 3)
                return 1
            return sum(walk(c) for c in node.values())

        self.assertGreater(walk(data), 100)

    def test_names_are_lowercase_slash_paths(self):
        tokens, _, _ = build_primitives(load_config(SAMPLE))
        for t in tokens:
            validate_path(t.path)
        self.assertIn("color/lays/primary/anchor", {t.path for t in tokens})
        self.assertEqual(slugify("Lay's"), "lays")
        with self.assertRaises(ValueError):
            validate_path("color/Bad Name/1")
        with self.assertRaises(ValueError):
            validate_path("color/x[1]")

    def test_preset_merge_config_wins(self):
        cfg = load_config(SAMPLE)
        self.assertEqual(cfg["dimensions"], ["brand", "device"])  # from preset
        self.assertEqual(cfg["base_mode"], "include")  # config overrides preset's "ask"
        self.assertEqual(cfg["tiers"]["component_tokens"], "minimal")  # skill default


if __name__ == "__main__":
    unittest.main()
