import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "design-system-definer"
sys.path.insert(0, str(SKILL / "scripts"))
SAMPLE = SKILL / "examples" / "multi-brand-sample.yaml"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "multi-brand-ds.reference.json"
