"""Every built-in dimension, brand x theme layering, custom dimensions and inheritance."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _path
from _path import SAMPLE, SKILL
from build import generate, main, render_files
from config import load_config
from model import Alias

BRAND = """
brands:
  - name: Acme
    anchors: { blue: "#2563EB" }
"""
TWO = """
brands:
  - name: Acme
    anchors: { blue: "#2563EB" }
  - name: Zest
    anchors: { orange: "#FFB400" }
    neutral: warm
"""


def build(text, extra=""):
    d = tempfile.mkdtemp()
    p = Path(d) / "c.yaml"
    p.write_text(text + extra, encoding="utf-8")
    return generate(p)


def by(cols):
    return {c.name: c for c in cols}


def passing(results):
    return [r for r in results if not r.passed] == []


class BrandTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.prims, cls.cols, cls.results, cls.notes = build(
            "preset: brand-theme-white-label\nbase_mode: include\n" + TWO)
        cls.by = by(cls.cols)

    def test_layers_and_order(self):
        self.assertEqual([c.name for c in self.cols], ["Primitives", "Device", "Brand", "Theme"])
        self.assertEqual(self.by["Brand"].modes, ["Base", "Acme", "Zest"])
        self.assertEqual(self.by["Theme"].modes, ["Light", "Dark"])

    def test_theme_aliases_brand_palette(self):
        v = self.by["Theme"].get("color/action/primary/default").values
        self.assertEqual(v["Light"], Alias("palette/light/color/action/primary/default", "Brand"))
        self.assertEqual(v["Dark"], Alias("palette/dark/color/action/primary/default", "Brand"))
        brand = self.by["Brand"].get("palette/dark/color/action/primary/default")
        self.assertEqual(set(brand.values), {"Base", "Acme", "Zest"})

    def test_contrast_checked_for_every_brand_and_theme(self):
        modes = {r.mode for r in self.results}
        self.assertTrue({"Acme / Light", "Acme / Dark", "Zest / Light", "Zest / Dark", "Base / Dark"} <= modes)
        self.assertTrue(passing(self.results))

    def test_components_bind_theme_names_only(self):
        # canonical names live in Theme; the Brand layer uses palette/ prefixes
        self.assertNotIn("color/surface/page", self.by["Brand"].paths())
        self.assertIn("color/surface/page", self.by["Theme"].paths())

    def test_every_alias_target_exists_and_comes_earlier(self):
        order = {c.name: i for i, c in enumerate(self.cols)}
        index = {c.name: set(c.paths()) for c in self.cols}
        for c in self.cols:
            for v in c.variables:
                for val in v.values.values():
                    if isinstance(val, Alias):
                        self.assertIn(val.target, index[val.collection], f"{c.name}:{v.path}")
                        if val.collection != c.name:
                            self.assertLess(order[val.collection], order[c.name])


class Platform(unittest.TestCase):
    def test_platform_owns_control_size_and_duration(self):
        cfg, prims, cols, results, _ = build("preset: multi-platform\n" + BRAND)
        b = by(cols)
        self.assertEqual(b["Platform"].modes, ["Web", "iOS", "Android"])
        control = b["Platform"].get("size/control").values
        self.assertEqual([control[m].target for m in ("Web", "iOS", "Android")], ["size/44", "size/44", "size/48"])
        self.assertIn("duration/short", b["Platform"].paths())
        self.assertTrue(passing(results))


class Density(unittest.TestCase):
    def test_density_owns_rhythm(self):
        cfg, prims, cols, results, _ = build("preset: responsive-density\n" + BRAND)
        b = by(cols)
        self.assertEqual(b["Density"].modes, ["Compact", "Comfortable", "Spacious"])
        self.assertEqual([b["Density"].get("space/stack").values[m].target for m in b["Density"].modes],
                         ["space/8", "space/16", "space/24"])
        self.assertIn("space/inset", b["Density"].paths())
        self.assertNotIn("space/section", b["Brand"].paths())
        self.assertTrue(passing(results))


class A11y(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.prims, cls.cols, cls.results, cls.notes = build("preset: accessibility-variants\n" + BRAND)
        cls.by = by(cls.cols)

    def test_large_text_enlarges_uniform_sizes_and_inherits_the_rest(self):
        a = self.by["A11y"].get("type/size/body-m").values
        self.assertEqual(a["Default"], Alias("device/type/size/body-m", "Device"))
        self.assertEqual(a["Large text"], Alias("font/size/20", "Primitives"))  # 16 x 1.25
        heading = self.by["A11y"].get("type/size/heading-xl").values
        self.assertEqual(heading["Large text"], Alias("device/type/size/heading-xl", "Device"))  # varies by device

    def test_reduced_motion_zeroes_durations(self):
        d = self.by["A11y"].get("duration/medium").values
        self.assertEqual(d["Reduced motion"], Alias("duration/0", "Primitives"))
        self.assertEqual(d["Default"], Alias("brand/duration/medium", "Brand"))

    def test_large_text_widens_focus_ring(self):
        f = self.by["A11y"].get("border-width/focus").values
        self.assertEqual(f["Large text"], Alias("border/3", "Primitives"))

    def test_text_styles_bind_the_top_layer(self):
        from export_figma import text_style_defs
        styles = {s["name"]: s for s in text_style_defs(self.cols, self.cfg)}
        self.assertEqual(styles["Body/M"]["bind"]["collection"]["fontSize"], "A11y")
        self.assertEqual(styles["Body/M"]["size"], 16)
        self.assertTrue(passing(self.results))


class ProductMarketing(unittest.TestCase):
    def test_marketing_type_tokens_and_styles(self):
        cfg, prims, cols, results, _ = build("preset: product-marketing\n" + BRAND)
        device = by(cols)["Device"]
        self.assertIn("type/size/marketing-display-xl", device.paths())
        names = [s[0] for s in cfg["type"]["styles"]]
        self.assertIn("Marketing/Display XL", names)
        self.assertNotIn("Context", by(cols))  # context adds tokens, not a collection
        from export_figma import text_style_defs
        styles = {s["name"]: s for s in text_style_defs(cols, cfg)}
        self.assertEqual(styles["Marketing/Display XL"]["size"], 40)
        self.assertTrue(passing(results))


class Locale(unittest.TestCase):
    def test_family_override_and_direction(self):
        cfg, prims, cols, results, _ = build("preset: multi-locale\n" + BRAND)
        loc = by(cols)["Locale"]
        fam = loc.get("type/family/body").values
        self.assertEqual(fam["Latin"], Alias("brand/type/family/body", "Brand"))
        self.assertEqual(fam["Japanese"], Alias("font/family/noto-sans-jp", "Primitives"))
        self.assertEqual(loc.get("layout/direction").values["Arabic"], "rtl")
        self.assertIn("font/family/noto-sans-arabic", prims.values)
        self.assertTrue(passing(results))


class HouseOfBrands(unittest.TestCase):
    def test_sub_brand_inherits_and_overrides(self):
        text = """
preset: house-of-brands
brands:
  - name: Master
    anchors: { blue: "#2563EB" }
    fonts: { heading: Lora, body: Figtree }
    radius: { button: 4, field: 4, card: 4, control: 2 }
  - name: Kids
    extends: Master
    anchors: { blue: "#FFB400" }
    radius: { button: 16, field: 16, card: 16, control: 8 }
"""
        cfg, prims, cols, results, _ = build(text)
        kids = next(b for b in cfg["brands"] if b["name"] == "Kids")
        self.assertEqual(kids["fonts"], {"heading": "Lora", "body": "Figtree"})  # inherited
        self.assertEqual(kids["radius"]["button"], 16)  # overridden
        self.assertEqual(kids["anchors"]["blue"], "#FFB400")
        self.assertEqual(by(cols)["Brand"].modes, ["Master", "Kids"])
        self.assertTrue(passing(results))

    def test_unknown_parent_and_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.yaml"
            p.write_text("brands:\n  - name: A\n    extends: Nope\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown brand"):
                load_config(p)
            p.write_text("dimensions: [brand]\nbase_mode: none\nbrands:\n  - {name: A, extends: B}\n  - {name: B, extends: A}\n",
                         encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cycle"):
                load_config(p)


class Custom(unittest.TestCase):
    TEXT = BRAND + """
custom_dimensions:
  - name: Season
    modes: [Summer, Winter]
    tokens:
      space/season-gap:
        values: { Summer: space/16, Winter: space/24 }
      color/season-accent:
        type: color
        values: { Summer: color/white, Winter: color/black }
"""

    def test_custom_dimension_becomes_a_collection(self):
        cfg, prims, cols, results, _ = build(self.TEXT)
        season = by(cols)["Season"]
        self.assertEqual(season.modes, ["Summer", "Winter"])
        self.assertEqual(season.get("space/season-gap").values["Winter"], Alias("space/24", "Primitives"))
        self.assertEqual(season.get("color/season-accent").values["Winter"], Alias("color/black", "Primitives"))

    def test_custom_token_must_alias_a_primitive(self):
        bad = BRAND + "custom_dimensions:\n  - name: S\n    modes: [A]\n    tokens:\n      x/y: { values: { A: space/999 } }\n"
        with self.assertRaisesRegex(ValueError, "not a primitive"):
            build(bad)

    def test_custom_dimension_name_cannot_shadow_builtin(self):
        bad = BRAND + "custom_dimensions:\n  - name: Brand\n    modes: [A]\n    tokens:\n      x/y: { values: { A: space/16 } }\n"
        with self.assertRaisesRegex(ValueError, "built-in"):
            build(bad)

    def test_custom_exports_build(self):
        files = render_files(*build(self.TEXT))
        self.assertTrue(any("Season" in k for k in files))


class AllDimensions(unittest.TestCase):
    """Everything on at once: layering, ordering, exports."""

    TEXT = """
dimensions: [brand, theme, device, platform, density, a11y, context, locale]
base_mode: include
tiers: { component_tokens: full }
""" + TWO

    @classmethod
    def setUpClass(cls):
        cls.parts = build(cls.TEXT)
        cls.cfg, cls.prims, cls.cols, cls.results, cls.notes = cls.parts

    def test_builds_and_passes(self):
        self.assertTrue(passing(self.results))
        names = [c.name for c in self.cols]
        self.assertEqual(names[0], "Primitives")
        for expected in ("Device", "Platform", "Density", "A11y", "Locale", "Brand", "Theme"):
            self.assertIn(expected, names)

    def test_no_duplicate_paths_per_collection_and_no_orphan_layers(self):
        for c in self.cols:
            self.assertEqual(len(c.paths()), len(set(c.paths())), c.name)
        referenced = {(v.collection, v.target) for c in self.cols for var in c.variables
                      for v in var.values.values() if isinstance(v, Alias)}
        for c in self.cols:
            for var in c.variables:
                for prefix in ("brand/", "device/", "platform/", "a11y/", "palette/"):
                    if var.path.startswith(prefix):
                        self.assertIn((c.name, var.path), referenced, f"orphan layer token {c.name}:{var.path}")

    def test_scripts_parse_and_fit(self):
        files = render_files(*self.parts)
        scripts = {k: v for k, v in files.items() if k.startswith("figma-build/")}
        order = sorted(scripts)
        self.assertRegex(order[0], r"01-primitives")
        node = shutil.which("node")
        for name, body in scripts.items():
            self.assertLess(len(body), 50000, name)
            if node:
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "x.js"
                    p.write_text("async function w(figma){\n" + body + "\n}", encoding="utf-8")
                    r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")

    def test_style_dictionary_caps_combinations(self):
        body = render_files(*self.parts)["dtcg/sd.config.mjs"]
        self.assertIn("First 256 combinations only", body)

    def test_text_styles_resolve(self):
        from export_figma import text_style_defs
        styles = text_style_defs(self.cols, self.cfg)
        self.assertEqual(len(styles), len(self.cfg["type"]["styles"]))
        self.assertTrue(all(isinstance(s["size"], (int, float)) and isinstance(s["family"], str) for s in styles))


class Presets(unittest.TestCase):
    def test_every_preset_builds_with_zero_failures(self):
        for p in sorted((SKILL / "presets").glob("*.yaml")):
            brands = TWO if p.stem in ("multi-brand-white-label", "brand-theme-white-label", "house-of-brands") else BRAND
            extra = "base_mode: none\n" if p.stem in ("multi-brand-white-label", "brand-theme-white-label") else ""
            cfg, prims, cols, results, _ = build(f"preset: {p.stem}\n{extra}{brands}")
            self.assertTrue(passing(results), p.stem)

    def test_cli_approved_run_for_a_new_dimension(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "c.yaml"
            cfg.write_text("preset: accessibility-variants\n" + BRAND, encoding="utf-8")
            self.assertEqual(main([str(cfg), "--approve", "--out", str(Path(d) / "o")]), 0)
            self.assertTrue((Path(d) / "o" / "figma-build").exists())


if __name__ == "__main__":
    unittest.main()
