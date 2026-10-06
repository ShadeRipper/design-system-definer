"""Build dist/design-system-definer.skill: a zip with the skill folder at its root.

Upload it in Claude (Settings > Capabilities > Skills) for claude.ai or Claude Desktop.
Run from anywhere: python tools/package.py
"""
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "define"
OUT = REPO / "dist" / "design-system-definer.skill"


def main():
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SKILL.rglob("*")):
            if p.is_dir() or "__pycache__" in p.parts or p.suffix == ".pyc":
                continue
            z.write(p, Path(SKILL.name) / p.relative_to(SKILL))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
