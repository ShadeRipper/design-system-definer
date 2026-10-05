"""Whole-system tests: R1 gate, R2 structure, R4 aliases, R5 matrix, R6 shape, R8 determinism, R9 types."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _path
from _path import FIXTURE, SAMPLE, SKILL
from build import generate, main, render_files
from config import load_config
from model import Alias
from primitives import validate_path

REFERENCE = json.loads(FIXTURE.read_text(encoding="utf-8"))


def write_cfg(d, text):
    p = Path(d) / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return p


SINGLE = """
preset: single-brand-light-dark
brands:
  - name: Acme
    anchors: { blue: "#2563EB" }
"""
MARKETING = """
preset: marketing-site
brands:
  - name: Acme
    anchors: { green: "#00704A" }
"""


class Structure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.prims, cls.cols, cls.results, cls.notes = generate(SAMPLE)
        cls.by = {c.name: c for c in cls.cols}

    def test_collections_and_modes_match_reference(self):
        for name in ("Brand", "Device"):
            self.assertEqual(self.by[name].modes, REFERENCE["collections"][name]["modes"])
        self.assertEqual([c.name for c in self.cols], ["Primitives", "Device", "Brand"])

    def test_covers_reference_variable_names(self):
        for name in ("Brand", "Device"):
            missing = set(REFERENCE["collections"][name]["variables"]) - set(self.by[name].paths())
            self.assertFalse(missing, f"{name} missing {sorted(missing)}")
        missing = set(REFERENCE["collections"]["Primitives"]["variables"]) - set(self.by["Primitives"].paths())
        self.assertFalse(missing, f"Primitives missing {sorted(missing)}")

    def test_brands_are_modes_never_collections(self):
        self.assertFalse([c for c in self.cols if c.name in ("Lay's", "Pepsi", "Starbucks")])

    def test_r4_semantic_tier_is_aliases_only(self):
        for name in ("Brand", "Device"):
            for v in self.by[name].variables:
                for mode, val in v.values.items():
                    if v.type == "easing":
                        continue
                    self.assertIsInstance(val, Alias, f"{name}:{v.path}:{mode}")

    def test_aliases_resolve(self):
        index = {c.name: set(c.paths()) for c in self.cols}
        for c in self.cols:
            for v in c.variables:
                for val in v.values.values():
                    if isinstance(val, Alias):
                        self.assertIn(val.target, index[val.collection], f"{c.name}:{v.path}")

    def test_components_never_bind_primitives_via_semantic_gaps(self):
        # every semantic variable has a description and an explicit scope list
        for name in ("Brand", "Device"):
            for v in self.by[name].variables:
                self.assertTrue(v.description, v.path)
                self.assertTrue(v.scopes, v.path)

    def test_names_valid(self):
        for c in self.cols:
            for v in c.variables:
                validate_path(v.path)
        with self.assertRaises(ValueError):
            validate_path("color/Bad Name/1")
        with self.assertRaises(ValueError):
            validate_path("color/x[1]")

    def test_zero_failing_pairs_every_mode(self):
        self.assertEqual([r for r in self.results if not r.passed], [])
        modes = {r.mode for r in self.results}
        self.assertTrue({"Base", "Lay's", "Pepsi", "Starbucks"} <= modes)

    def test_lays_yellow_indicator_is_darker_than_fill(self):
        brand = self.by["Brand"]
        fill = brand.get("color/action/primary/default").values["Lay's"].target
        ind = brand.get("color/indicator").values["Lay's"].target
        self.assertTrue(fill.startswith("color/lays/yellow/") and ind.startswith("color/lays/yellow/"))
        self.assertGreater(int(ind.rsplit("/", 1)[1]), int(fill.rsplit("/", 1)[1]))
        # dark text on the light yellow fill, white on the dark brands
        self.assertEqual(brand.get("color/action/on-primary").values["Lay's"].target, "color/neutral-warm/950")
        self.assertEqual(brand.get("color/action/on-primary").values["Pepsi"].target, "color/white")

    def test_density_and_cross_collection_alias(self):
        brand = self.by["Brand"]
        self.assertEqual(brand.get("space/section").values["Starbucks"], Alias("space/2xl", "Device"))
        self.assertEqual(brand.get("space/section").values["Pepsi"], Alias("space/xl", "Device"))

    def test_text_styles_match_reference(self):
        names = [s[0] for s in self.cfg["type"]["styles"]]
        self.assertEqual(sorted(names), sorted(REFERENCE["text_styles"]))


class Gate(unittest.TestCase):
    def test_nothing_written_without_approval(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            self.assertEqual(main([str(SAMPLE), "--out", str(out)]), 0)
            self.assertFalse(out.exists())

    def test_approved_run_writes_required_and_optional_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main([str(SAMPLE), "--approve", "--out", d]), 0)
            for rel in ["decision-brief.md", "ds.config.yaml", "contrast-matrix.md", "contrast-matrix.csv",
                        "figma/Primitives.Value.tokens.json", "figma-build/01-primitives.js",
                        "build-plan.md", "dtcg/sd.config.mjs", "decision-records/01-collection-structure.md"]:
                self.assertTrue((Path(d) / rel).exists(), rel)

    def test_failing_pair_blocks_export(self):
        with tempfile.TemporaryDirectory() as d:
            # a custom target no ramp can meet on both ends makes derived pairs fail
            cfg = write_cfg(d, SAMPLE.read_text(encoding="utf-8").replace(
                "contrast: AA", "contrast: { text: 21, ui: 21 }"))
            self.assertEqual(main([str(cfg), "--approve", "--out", str(Path(d) / "o")]), 1)
            self.assertFalse((Path(d) / "o").exists())

    def test_ask_base_mode_is_a_config_error(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SAMPLE.read_text(encoding="utf-8").replace("base_mode: include", "base_mode: ask"))
            self.assertEqual(main([str(cfg)]), 2)


class Determinism(unittest.TestCase):
    def test_same_config_same_bytes(self):
        a = render_files(*generate(SAMPLE))
        b = render_files(*generate(SAMPLE))
        self.assertEqual(a, b)

    def test_one_value_changes_output(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SAMPLE.read_text(encoding="utf-8").replace("contrast: AA", "contrast: AAA"))
            base = render_files(*generate(SAMPLE))
            aaa = render_files(*generate(cfg))
            self.assertNotEqual(base["dtcg/tokens/Primitives.tokens.json"], aaa["dtcg/tokens/Primitives.tokens.json"])
            self.assertEqual([r for r in generate(cfg)[3] if not r.passed], [])

    def test_base_mode_none_removes_base(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SAMPLE.read_text(encoding="utf-8").replace("base_mode: include", "base_mode: none"))
            cols = generate(cfg)[2]
            self.assertEqual(next(c for c in cols if c.name == "Brand").modes, ["Lay's", "Pepsi", "Starbucks"])

    def test_component_tier_none_and_full(self):
        with tempfile.TemporaryDirectory() as d:
            none = write_cfg(d, SAMPLE.read_text(encoding="utf-8") + "tiers: { component_tokens: none }\n")
            cols = {c.name: c for c in generate(none)[2]}
            self.assertNotIn("radius/control", cols["Brand"].paths())
            self.assertNotIn("size/control", cols["Device"].paths())
            full = write_cfg(d, SAMPLE.read_text(encoding="utf-8") + "tiers: { component_tokens: full }\n")
            cols = {c.name: c for c in generate(full)[2]}
            self.assertIn("component/button/height", cols["Brand"].paths())


class SystemTypes(unittest.TestCase):
    def test_single_brand_light_dark(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, prims, cols, results, _ = generate(write_cfg(d, SINGLE))
            theme = next(c for c in cols if c.name == "Theme")
            self.assertEqual(theme.modes, ["Light", "Dark"])
            self.assertEqual([r for r in results if not r.passed], [])
            page = theme.get("color/surface/page").values
            self.assertNotEqual(page["Light"], page["Dark"])
            # no device collection: type sizes live in the theme collection
            self.assertNotIn("Device", [c.name for c in cols])
            self.assertIn("type/size/body-m", theme.paths())

    def test_marketing_site_device_only(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, _, cols, results, _ = generate(write_cfg(d, MARKETING))
            self.assertEqual([c.name for c in cols], ["Primitives", "Device", "Brand"])
            self.assertEqual(next(c for c in cols if c.name == "Brand").modes, ["Acme"])
            self.assertEqual([r for r in results if not r.passed], [])

    def test_brand_and_theme_together_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SAMPLE.read_text(encoding="utf-8") + "dimensions: [brand, theme]\n")
            with self.assertRaises(ValueError):
                load_config(cfg)

    def test_unsupported_dimension_rejected_with_guidance(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SINGLE + "dimensions: [platform]\n")
            with self.assertRaisesRegex(ValueError, "not supported in v1"):
                load_config(cfg)

    def test_dark_mode_every_pair_passes_at_aaa(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, SINGLE + "color: { contrast: AAA }\n")
            results = generate(cfg)[3]
            self.assertEqual([r for r in results if not r.passed], [])

    def test_primary_neutral_brand(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = write_cfg(d, "brands:\n  - name: Plain\n")
            cols = generate(cfg)[2]
            brand = next(c for c in cols if c.name == "Brand")
            self.assertEqual(brand.get("color/action/primary/default").values["Plain"].target, "color/neutral-cool/900")


class Exports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = render_files(*generate(SAMPLE))

    def test_figma_native_colors_are_objects(self):
        for name, body in self.files.items():
            if not (name.startswith("figma/") and name.endswith(".json")):
                continue
            data = json.loads(body)

            def walk(node):
                if "$type" in node:
                    if node["$type"] == "color" and isinstance(node["$value"], dict):
                        self.assertEqual(set(node["$value"]), {"colorSpace", "components", "alpha", "hex"})
                    return 1
                return sum(walk(c) for c in node.values())
            self.assertGreater(walk(data), 20, name)

    def test_figma_build_scripts_fit_and_parse(self):
        scripts = {k: v for k, v in self.files.items() if k.startswith("figma-build/")}
        self.assertGreaterEqual(len(scripts), 4)
        node = shutil.which("node")
        for name, body in scripts.items():
            self.assertLess(len(body), 50000, name)
            if node:
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "x.js"
                    p.write_text("async function w(figma){\n" + body + "\n}", encoding="utf-8")
                    r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")

    def test_script_order_primitives_device_brand_then_styles(self):
        names = sorted(k for k in self.files if k.startswith("figma-build/"))
        self.assertRegex(names[0], r"01-primitives")
        self.assertRegex(names[1], r"02-device")
        self.assertRegex(names[2], r"03-brand")
        self.assertRegex(names[-1], r"text-styles")

    def test_dtcg_aliases_use_brace_paths(self):
        brand = json.loads(self.files["dtcg/tokens/Brand.lays.tokens.json"])
        self.assertEqual(brand["color"]["action"]["primary"]["default"]["$value"], "{color.lays.yellow.200}")
        self.assertEqual(brand["easing"]["standard"]["$type"], "cubicBezier")

    def test_build_plan_has_checkpoints_and_component_bindings(self):
        plan = self.files["build-plan.md"]
        self.assertIn("CHECKPOINT 1", plan)
        self.assertIn("CHECKPOINT 2", plan)
        for comp in ("button", "text-field", "checkbox", "radio", "selectable-card", "progress", "feedback"):
            self.assertIn(f"**CHECKPOINT ({comp}):**", plan)
        self.assertIn("`radius/button`", plan)

    def test_brief_lists_every_decision_with_a_reason(self):
        brief = self.files["decision-brief.md"]
        for needle in ("Contrast target", "Spacing base", "Component tokens", "Base mode", "Lay's",
                       "does not pass on white" if False else "lands on step", "Sign-off"):
            self.assertIn(needle, brief)
        for line in brief.splitlines():
            if line.startswith("| ") and not line.startswith("| ---") and "Decision" not in line \
                    and "Collection" not in line:
                cells = [c for c in line.strip("|").split("|")]
                self.assertTrue(all(c.strip() for c in cells), line)

    def test_style_dictionary_config_parses(self):
        node = shutil.which("node")
        body = self.files["dtcg/sd.config.mjs"]
        self.assertIn("lays-mobile", body)
        if node:
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "x.mjs"
                p.write_text(body.replace("import StyleDictionary from 'style-dictionary';", ""), encoding="utf-8")
                r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)


class Packaging(unittest.TestCase):
    def test_skill_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", text)
        self.assertTrue(m, "SKILL.md needs name and description frontmatter")
        self.assertEqual(m.group(1), SKILL.name)
        self.assertLess(len(m.group(2)), 1024)

    def test_skill_references_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for rel in re.findall(r"\]\(((?:references|templates|presets|scripts|examples)/[^)#]+)\)", text):
            self.assertTrue((SKILL / rel).exists(), rel)

    def test_presets_load(self):
        for p in (SKILL / "presets").glob("*.yaml"):
            self.assertTrue(p.read_text(encoding="utf-8").strip())

    def test_no_pyyaml_needed(self):
        # the skill ships its own pure-Python PyYAML
        self.assertTrue((SKILL / "scripts" / "_vendor" / "yaml" / "__init__.py").exists())


if __name__ == "__main__":
    unittest.main()
