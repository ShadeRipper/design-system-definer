"""R3 (ramps) and R5 (contrast): run `python -m unittest discover -s tests -v` from the repo root."""
import unittest

import _path  # noqa: F401
from color import contrast_ratio, hex_to_oklch, normalize_hex, oklch_to_hex
from config import resolve_contrast
from contrast import check_pair
from ramps import WHITE, generate_ramp

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
        r = generate_ramp("#FFC72C", STEPS, ui=3.0, text=4.5)
        self.assertEqual(r.anchor, "#FFC72C")
        self.assertLess(r.anchor_contrast_white, 3.0)
        self.assertEqual(r.safe_text, "black")
        self.assertGreaterEqual(r.anchor_contrast_black, 4.5)
        self.assertNotIn(r.anchor_step, (500, 600, 700, 800, 900, 950))
        self.assertEqual(r.steps[r.anchor_step], "#FFC72C")

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
                    self.assertEqual(r.anchor, normalize_hex(anchor))
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


if __name__ == "__main__":
    unittest.main()
