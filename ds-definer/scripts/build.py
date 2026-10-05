"""CLI: python build.py <config.yaml> --out <dir>

Deterministic: output depends only on the config. Exits 1 if any contrast pair fails.
"""
import argparse
import sys
from pathlib import Path

from config import load_config
from contrast import to_csv, to_markdown
from export_dtcg import export_dtcg
from export_figma import export_figma
from primitives import build_primitives


def build(config_path, out_dir):
    cfg = load_config(config_path)
    tokens, results, notes = build_primitives(cfg)
    out = Path(out_dir)
    files = {"contrast-matrix.md": to_markdown(results, notes),
             "contrast-matrix.csv": to_csv(results)}
    if "figma" in cfg["outputs"]:
        for name, body in export_figma(tokens).items():
            files[f"figma/{name}"] = body
    if "dtcg" in cfg["outputs"]:
        files["dtcg/tokens.json"] = export_dtcg(tokens)
    for rel, body in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    return results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    results = build(args.config, args.out)
    failing = [r for r in results if not r.passed]
    print(f"{len(results)} pairs checked, {len(failing)} failing -> {args.out}")
    for r in failing:
        print(f"  FAIL {r.id}: {r.ratio:.2f} < {r.required:g} (try {r.fix})")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
