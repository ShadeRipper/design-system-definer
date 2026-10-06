"""Optional third font role `ui`: navigation, buttons and list labels."""
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from build import generate
from export_figma import text_style_defs

BASE = "brands:\n  - name: Acme\n    anchors: { blue: \"#2563EB\" }\n"
UI = ("brands:\n  - name: Acme\n    anchors: { blue: \"#2563EB\" }\n"
      "    fonts: { heading: Inter, body: Inter, ui: Poppins }\n")


def build(text):
    p = Path(tempfile.mkdtemp()) / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return generate(p)


def names(cols):
    return {v.path for c in cols for v in c.variables}


class UiFont(unittest.TestCase):
    def test_off_by_default(self):
        cfg, _, cols, results, _ = build(BASE)
        self.assertNotIn("type/family/ui", names(cols))
        self.assertNotIn("type/weight/ui", names(cols))
        self.assertFalse(cfg["ui_font"])
        self.assertTrue(all(r.passed for r in results))

    def test_on_adds_family_and_weight(self):
        cfg, _, cols, _, _ = build(UI)
        self.assertIn("type/family/ui", names(cols))
        self.assertIn("type/weight/ui", names(cols))

    def test_label_styles_use_ui_role(self):
        cfg, _, cols, _, _ = build(UI)
        defs = {d["name"]: d for d in text_style_defs(cols, cfg)}
        self.assertEqual(defs["Label/M"]["family"], "Poppins")
        self.assertEqual(defs["Label/M"]["bind"]["family"], "type/family/ui")
        self.assertEqual(defs["Body/M"]["family"], "Inter")
        self.assertEqual(defs["Label/M"]["weight"], 500)

    def test_label_styles_use_ui_role_with_context(self):
        cfg, _, cols, _, _ = build("dimensions: [context]" + chr(10) + UI)
        defs = {d["name"]: d for d in text_style_defs(cols, cfg)}
        self.assertEqual(defs["Label/S"]["family"], "Poppins")
        self.assertTrue(any(n.startswith("Marketing/") for n in defs))
        self.assertEqual(defs["Marketing/Display XL"]["family"], "Inter")

    def test_second_brand_without_ui_falls_back_to_body(self):
        two = UI + "  - name: Zest\n    anchors: { orange: \"#FFB400\" }\n    neutral: warm\n"
        cfg, _, cols, _, _ = build("dimensions: [brand]\nbase_mode: none\n" + two)
        self.assertEqual({b["name"]: b["fonts"]["ui"] for b in cfg["brands"]}, {"Acme": "Poppins", "Zest": "Inter"})

    def test_style_cannot_use_ui_when_off(self):
        text = BASE + "type:\n  styles:\n    - [Nav/Label, body-m, ui, ui]\n"
        with self.assertRaises(ValueError):
            build(text)


class StatusRoles(unittest.TestCase):
    def test_success_can_use_its_own_hue(self):
        text = BASE + "color:" + chr(10) + "  status: { cyan: \"#0891B2\" }" + chr(10) + "  status_roles: { success: cyan }" + chr(10)
        cfg, _, cols, results, _ = build(text)
        n = names(cols)
        self.assertIn("color/cyan/600", n)
        self.assertNotIn("color/green/600", n)
        self.assertTrue(all(r.passed for r in results))

    def test_role_pointing_at_missing_hue_is_an_error(self):
        with self.assertRaises(ValueError):
            build(BASE + "color:" + chr(10) + "  status_roles: { success: lime }" + chr(10))


class InverseRoles(unittest.TestCase):
    def test_roles_exist_and_pass(self):
        cfg, _, cols, results, _ = build(BASE)
        n = names(cols)
        for role in ("color/surface/inverse", "color/surface/brand-deep", "color/surface/brand-subtle",
                     "color/text/inverse", "color/text/brand"):
            self.assertIn(role, n)
        self.assertTrue(all(r.passed for r in results))
        self.assertTrue(any("text/inverse on color/surface/brand-deep" in r.id for r in results))


if __name__ == "__main__":
    unittest.main()
