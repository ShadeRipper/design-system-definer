"""Delta build scripts: only what changed between two builds.

After you change the config and rebuild, the full Figma scripts would rewrite every variable. The
delta scripts carry only new or changed variables and text styles, so the second run in Figma is
small. Scripts never delete: removed variables are listed in the delta README for you to remove.

  python build.py ds.config.yaml --approve --out ds-out --previous ds-out-v1
"""
import json
import re
from pathlib import Path

DATA_RE = re.compile(r"^const DATA = (.*);$", re.M)


def _parse(files):
    """{collection: {path: var}}, {style name: style}, per script file."""
    cols, styles = {}, {}
    for body in files.values():
        m = DATA_RE.search(body)
        if not m:
            continue
        data = json.loads(m.group(1))
        for c in data.get("collections", []):
            cols.setdefault(c["name"], {}).update({v["path"]: v for v in c["variables"]})
        for s in data.get("styles", []):
            styles[s["name"]] = s
    return cols, styles


def make_delta(old_files, new_files):
    """Return ({name: JS}, report). Both arguments map script file name to source."""
    old_cols, old_styles = _parse(old_files)
    out, report = {}, {"changed": {}, "removed": []}
    for name, body in new_files.items():
        m = DATA_RE.search(body)
        if not m:
            continue
        data = json.loads(m.group(1))
        changed = 0
        if "collections" in data:
            for c in data["collections"]:
                old = old_cols.get(c["name"], {})
                c["variables"] = [v for v in c["variables"] if old.get(v["path"]) != v]
                changed += len(c["variables"])
            data["collections"] = [c for c in data["collections"] if c["variables"]]
        if "styles" in data:
            data["styles"] = [s for s in data["styles"] if old_styles.get(s["name"]) != s]
            changed += len(data["styles"])
        if not changed:
            continue
        report["changed"][name] = changed
        out[name] = body[:m.start()] + "const DATA = " + json.dumps(data, ensure_ascii=False) + ";" + body[m.end():]
    new_cols, new_styles = _parse(new_files)
    for cname, vars_ in old_cols.items():
        report["removed"] += [f"{cname}::{p}" for p in vars_ if p not in new_cols.get(cname, {})]
    report["removed"] += [f"text style {n}" for n in old_styles if n not in new_styles]
    return out, report


def delta_readme(report):
    lines = ["# Delta build", "",
             "Run these scripts in file order through `use_figma`. They create or update only what changed since the previous build.", ""]
    if report["changed"]:
        lines += ["| Script | New or changed |", "| --- | --- |"] + [f"| `{n}` | {c} |" for n, c in sorted(report["changed"].items())]
    else:
        lines.append("Nothing changed.")
    if report["removed"]:
        lines += ["", "Removed from the config but **not deleted** in Figma (scripts never delete). Remove by hand if unused:", ""]
        lines += [f"- {r}" for r in report["removed"]]
    return "\n".join(lines) + "\n"


def load_scripts(build_dir):
    d = Path(build_dir) / "figma-build"
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("*.js"))} if d.is_dir() else {}
