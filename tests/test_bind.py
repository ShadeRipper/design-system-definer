"""Binding scripts for existing designs, and delta builds."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _path  # noqa: F401
from build import generate, main, render_files
from delta import make_delta

BASE = ("outputs: [figma, dtcg, decision-records, build-plan, bind]\n"
        "brands:\n  - name: Acme\n    anchors: { blue: \"#2563EB\" }\n    fonts: { heading: Inter, body: Inter, ui: Poppins }\n")


def build(text):
    p = Path(tempfile.mkdtemp()) / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return generate(p)


def node_ok(source):
    """Syntax-check a use_figma script (top-level await and return are legal there)."""
    if not shutil.which("node"):
        return True
    f = Path(tempfile.mkdtemp()) / "s.js"
    f.write_text("(async () => {\n" + source + "\n})();", encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
    return r.returncode == 0 or r.stderr


class BindScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = render_files(*build(BASE))

    def test_written_only_when_asked(self):
        plain = render_files(*build(BASE.replace(", bind]", "]")))
        self.assertFalse([k for k in plain if k.startswith("figma-bind/")])
        self.assertTrue([k for k in self.files if k.startswith("figma-bind/")])

    def test_config_comes_from_tokens_not_hardcoded(self):
        body = self.files["figma-bind/01-bind-styles-colours-radius.js"]
        self.assertIn("Brand::color/text/primary", body)
        self.assertIn("color/acme/blue", body)
        self.assertIn('"uiFamily": "Poppins"', body)
        self.assertNotIn("drishtiq", body.lower())

    def test_run_header_is_a_dry_run_by_default(self):
        for n in ("01-bind-styles-colours-radius.js", "02-structure.js"):
            body = self.files["figma-bind/" + n]
            self.assertIn("const APPLY_FLAG = false;", body)
            self.assertIn("REPLACE_WITH_PAGE_ID", body)

    def test_scripts_are_valid_javascript(self):
        for n, body in self.files.items():
            if n.startswith("figma-bind/") and n.endswith(".js"):
                self.assertIs(node_ok(body), True, n)

    def test_style_table_lists_every_text_style(self):
        body = self.files["figma-bind/01-bind-styles-colours-radius.js"]
        for name in ("Heading/Display", "Body/M", "Label/M"):
            self.assertIn(f'"name": "{name}"', body)

    def test_spacing_prefers_semantic_steps(self):
        body = self.files["figma-bind/02-structure.js"]
        self.assertRegex(body, r'"16": "(Brand|Device)::space/md"')   # semantic step, not the primitive


class AuditAndInventory(unittest.TestCase):
    def test_audit_is_generated_and_read_only(self):
        files = render_files(*build(BASE))
        body = files["figma-bind/03-audit.js"]
        self.assertIn("coverage", body)
        for write in (".setTextStyleIdAsync", ".setBoundVariable(", ".fills =", ".name ="):
            self.assertNotIn(write, body)  # the audit never writes

    def test_inventory_template_is_standalone_and_read_only(self):
        src = (Path(__file__).resolve().parent.parent / "skills" / "define" / "templates" / "inventory.js").read_text(encoding="utf-8")
        self.assertNotIn("CONFIG", src)  # runs before any config exists
        for write in (".setTextStyleIdAsync", ".setBoundVariable(", ".fills =", ".name ="):
            self.assertNotIn(write, src)
        self.assertIs(node_ok(src), True)

    def test_web_product_and_site_preset_builds_clean(self):
        nl = chr(10)
        cfg, _, cols, results, _ = build(nl.join(["preset: web-product-and-site", "brands:", "  - name: Acme", "    anchors: { green: '#0AC28C' }", ""]))
        self.assertTrue(all(r.passed for r in results))
        names = {v.path for c in cols for v in c.variables}
        self.assertIn("type/size/marketing-display-xl", names)


class Delta(unittest.TestCase):
    def test_only_new_and_changed_items_are_emitted(self):
        old = render_files(*build(BASE))
        newer = render_files(*build(BASE + "type:\n  styles:\n    - [Heading/Display, display, heading, heading]\n    - [Body/M Strong, body-m, body, heading]\n"))
        o = {k.split("/", 1)[1]: v for k, v in old.items() if k.startswith("figma-build/")}
        n = {k.split("/", 1)[1]: v for k, v in newer.items() if k.startswith("figma-build/")}
        delta, report = make_delta(o, n)
        self.assertTrue(any(name.endswith("text-styles.js") for name in delta))
        styles = delta[next(k for k in delta if k.endswith("text-styles.js"))]
        self.assertIn("Body/M Strong", styles)
        self.assertNotIn('"Body/L"', styles)  # unchanged styles are left out
        self.assertTrue(report["removed"])  # old default styles are no longer in the config

    def test_identical_builds_have_no_delta(self):
        a = render_files(*build(BASE))
        o = {k.split("/", 1)[1]: v for k, v in a.items() if k.startswith("figma-build/")}
        delta, report = make_delta(o, dict(o))
        self.assertEqual(delta, {})
        self.assertEqual(report["removed"], [])

    def test_cli_previous_writes_delta_folder(self):
        d = Path(tempfile.mkdtemp())
        cfg = d / "c.yaml"
        cfg.write_text(BASE, encoding="utf-8")
        self.assertEqual(main([str(cfg), "--approve", "--out", str(d / "v1")]), 0)
        cfg.write_text(BASE.replace("#2563EB", "#1D4ED8"), encoding="utf-8")
        self.assertEqual(main([str(cfg), "--approve", "--out", str(d / "v2"), "--previous", str(d / "v1")]), 0)
        self.assertTrue((d / "v2" / "figma-build-delta" / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
