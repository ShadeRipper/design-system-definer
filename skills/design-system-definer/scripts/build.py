"""CLI for the Design System Definer.

  python build.py config.yaml                  playback: print the decision brief, write nothing
  python build.py config.yaml --approve --out DIR   write all outputs (after sign-off)

Deterministic: output depends only on the config. A failing contrast pair blocks export
(exit 1). Without --approve nothing is written, which enforces the sign-off rule (R1).
"""
import argparse
import sys
from pathlib import Path

from brief import build_brief, build_records
from build_plan import build_plan
from config import load_config
from contrast import to_csv, to_markdown
from delta import delta_readme, load_scripts, make_delta
from export_bind import export_bind_scripts
from export_dtcg import export_dtcg, style_dictionary_config
from export_figma import export_build_scripts, export_native_json, text_style_defs
from primitives import build_primitives
from semantic import build_collections, check_semantic, plan_tokens, requirements


def generate(config_path):
    cfg = load_config(config_path)
    plan = plan_tokens(cfg)
    prims = build_primitives(cfg, requirements(plan))
    sem_cols, derived = build_collections(cfg, prims, plan)
    prims.derived = derived
    collections = [prims.collection] + sem_cols
    sem_results, sem_notes = check_semantic(cfg, prims, derived)
    brand = next(c for c in collections if c.name == "Brand")
    results = prims.results + sem_results
    notes = prims.notes + brand.notes + sem_notes
    return cfg, prims, collections, results, notes


def render_files(cfg, prims, collections, results, notes):
    files = {"decision-brief.md": build_brief(cfg, prims, collections, results),
             "ds.config.yaml": cfg["_source_text"],
             "contrast-matrix.md": to_markdown(results, notes),
             "contrast-matrix.csv": to_csv(results)}
    outputs = cfg["outputs"]
    if "figma" in outputs:
        for name, body in export_native_json(collections).items():
            files[f"figma/{name}"] = body
        scripts = export_build_scripts(collections, cfg)
        for name, body in scripts.items():
            files[f"figma-build/{name}"] = body
    else:
        scripts = {}
    if "bind" in outputs:
        for name, body in export_bind_scripts(cfg, collections).items():
            files[f"figma-bind/{name}"] = body
    if "dtcg" in outputs:
        for name, body in export_dtcg(collections).items():
            files[f"dtcg/tokens/{name}"] = body
        files["dtcg/sd.config.mjs"] = style_dictionary_config(collections)
    if "decision-records" in outputs:
        for name, body in build_records(cfg, prims, collections).items():
            files[f"decision-records/{name}"] = body
    if "build-plan" in outputs:
        files["build-plan.md"] = build_plan(cfg, collections, list(scripts))
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--approve", action="store_true", help="designer signed off the brief; write files")
    ap.add_argument("--out", default="out")
    ap.add_argument("--previous", help="a previous build folder; also write figma-build-delta/ with only what changed")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        cfg, prims, collections, results, notes = generate(args.config)
    except ValueError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    failing = [r for r in results if not r.passed]
    if not args.approve:
        print(build_brief(cfg, prims, collections, results))
        print("\n(nothing written: re-run with --approve --out DIR after sign-off)")
        return 1 if failing else 0
    if failing:
        print(f"export blocked: {len(failing)} contrast pair(s) fail. Fix the config and re-run.", file=sys.stderr)
        for r in failing:
            print(f"  FAIL {r.id} ({r.mode}): {r.ratio:.2f} < {r.required:g}"
                  + (f" (try {r.fix})" if r.fix else ""), file=sys.stderr)
        return 1
    out = Path(args.out)
    files = render_files(cfg, prims, collections, results, notes)
    for rel, body in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    if args.previous:
        new_scripts = {k.split("/", 1)[1]: v for k, v in files.items() if k.startswith("figma-build/")}
        delta, report = make_delta(load_scripts(args.previous), new_scripts)
        for name, body in delta.items():
            p = out / "figma-build-delta" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8", newline=chr(10))
        (out / "figma-build-delta").mkdir(parents=True, exist_ok=True)
        (out / "figma-build-delta" / "README.md").write_text(delta_readme(report), encoding="utf-8", newline=chr(10))
        print(f"delta: {sum(report['changed'].values())} new or changed item(s) in {len(delta)} script(s)")
    print(f"{len(results)} pairs checked, 0 failing; wrote {len(files)} files to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
