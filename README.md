# Design System Definer

A Claude skill that turns a designer's brand thinking into an accessible, build-ready token foundation and a Figma build plan. Stage 1 of the workflow only: Figma builds the system, Claude Design imports the `.fig` file.

Full spec: [docs/PRD.md](docs/PRD.md).

## Status: build phase 1 (scripts and tests)

| Piece | State |
| --- | --- |
| OKLCH ramps calibrated to a contrast target (R3) | done, tested across a hue sweep and AA / AAA / custom |
| Contrast matrix with suggested fixes (R5) | done for primitives; semantic pairs arrive with `semantic.py` |
| Figma native variable JSON for primitives (R6) | written, **not yet validated** against a real Figma export fixture |
| DTCG export (P1) | done for primitives |
| Config + presets, deterministic reruns (R8) | done; 3 presets |
| Interview, `SKILL.md`, semantic tokens, build plan | later phases |

## Use

```bash
pip install -r requirements.txt
python ds-definer/scripts/build.py ds-definer/examples/multi-brand-sample.yaml --out out
python -m unittest discover -s ds-definer/tests -v
```

`build.py` exits 1 if any contrast pair fails. Output depends only on the config.

## Rules worth knowing

- **Contrast wins over anchor fidelity.** The exact anchor hex is always kept as `color/<brand>/<role>/anchor`. It also replaces its nearest ramp step, but only if that step still meets its requirement. Otherwise the ramp is calibrated and the anchor is flagged with a safe text pairing.
- **Contrast target is selectable:** `AA` (text 4.5, UI 3.0), `AAA` (7 / 4.5) or custom `{text, ui}`.
- **Names** are lowercase slash paths; spaces and brackets are rejected.
