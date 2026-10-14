"""Regression tests for the code-hygiene fixes: comment-safe collection names and a bounded
Style Dictionary combination list."""
import json
import re
import time
import unittest

import _path  # noqa: F401
from _path import SAMPLE
from build import generate
from export_dtcg import style_dictionary_config
from export_figma import export_build_scripts
from model import Collection, Variable

NOTE = "// First 256 combinations only; trim or extend this array as needed.\n"
MARKER = "hygiene/marker"
LINE_BREAKS = ("\n", "\r", "\r\n", "\u2028", "\u2029")


def _col(name, n_modes=1):
    modes = [f"m{i}" for i in range(n_modes)]
    return Collection(name, modes, [Variable(MARKER, "number", {m: 4 for m in modes})])


def _combos(config_js):
    return json.loads(re.search(r"const combos = (\[.*?\n\]);", config_js, re.S).group(1))


class CommentSafeName(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, _, cls.collections, _, _ = generate(SAMPLE)

    def _script_for(self, name):
        files = export_build_scripts(self.collections + [_col(name)], self.cfg)
        (script,) = [body for body in files.values() if MARKER in body]
        return script

    def test_normal_name_is_unchanged(self):
        first = self._script_for("Density").split("\n", 1)[0]
        self.assertEqual(first, "// Design System Definer: Density collection. Run with use_figma.")

    def test_line_breaks_cannot_end_the_comment(self):
        for sep in LINE_BREAKS:
            with self.subTest(sep=repr(sep)):
                lines = self._script_for(f"Brand{sep}alert(1) x").split("\n")
                self.assertEqual(
                    lines[0], "// Design System Definer: Brand alert(1) x collection. Run with use_figma.")
                # the next line is the data declaration, so nothing from the name escaped the comment
                self.assertTrue(lines[1].startswith("const DATA = "))
                for terminator in ("\r", "\u2028", "\u2029"):
                    self.assertNotIn(terminator, lines[0])


class BoundedCombinations(unittest.TestCase):
    def test_huge_product_is_capped_quickly(self):
        cols = [_col(f"Dim{i}", 4) for i in range(12)]  # 4**12 = 16.7 million combinations
        start = time.monotonic()
        out = style_dictionary_config(cols)
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(len(_combos(out)), 256)
        self.assertIn(NOTE, out)

    def test_exactly_cap_is_not_truncated(self):
        out = style_dictionary_config([_col(f"Dim{i}", 4) for i in range(4)])  # 4**4 = 256
        self.assertEqual(len(_combos(out)), 256)
        self.assertNotIn(NOTE, out)

    def test_one_over_cap_is_truncated(self):
        out = style_dictionary_config([_col("A", 257)])
        self.assertEqual(len(_combos(out)), 256)
        self.assertIn(NOTE, out)

    def test_small_product_is_complete(self):
        out = style_dictionary_config([_col("A", 3), _col("B", 2)])
        self.assertEqual(len(_combos(out)), 6)
        self.assertNotIn(NOTE, out)


if __name__ == "__main__":
    unittest.main()
