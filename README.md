# Design System Definer

A Claude skill that turns a designer's brand thinking into an accessible, build-ready token foundation and a Figma build plan. It covers stage 1 only (define); Figma builds the system and Claude Design imports the `.fig` file.

It interviews you one question at a time, plays back a decision brief for sign-off, then generates contrast-checked primitives and semantic tokens, Figma build scripts, a phased build plan and DTCG tokens. What it can and can't do: [docs/CAPABILITIES.md](docs/CAPABILITIES.md).

## How it works (30 seconds)

1. **Ask:** tell Claude *"Help me define a design system."*
2. **Answer:** a short interview, one question at a time. Claude explains why it asks.
3. **Approve:** read a one-page decision brief. Nothing is generated until you say yes.
4. **Build:** Claude creates the variables, modes and text styles in **any Figma file you can edit**.
5. **Use:** import the `.fig` into Claude Design, or take the code tokens.

Full walkthrough with examples and FAQ: **[docs/HOW-TO-USE.md](docs/HOW-TO-USE.md)**. Exactly what it covers and where it stops: **[docs/CAPABILITIES.md](docs/CAPABILITIES.md)**.

## Install

**Claude Code, as a plugin** (recommended; updates with the repo):

```
/plugin marketplace add ShadeRipper/design-system-definer
/plugin install design-system-definer@design-system-definer
```

**Claude Code, personal skill** (copies the folder to `~/.claude/skills`):

```bash
git clone https://github.com/ShadeRipper/design-system-definer && cd design-system-definer
sh install.sh            # macOS, Linux, Git Bash
./install.ps1            # Windows PowerShell
```

**claude.ai and Claude Desktop:** download `design-system-definer.skill` from the [latest release](https://github.com/ShadeRipper/design-system-definer/releases/latest) and upload it (Settings, Capabilities, Skills). To build it yourself: `python tools/package.py`.

Then ask: *"Help me define a design system."* Python 3.8+ is the only requirement; PyYAML is bundled.

## Use without Claude

```bash
cd skills/design-system-definer
python scripts/build.py examples/multi-brand-sample.yaml                 # playback: prints the decision brief, writes nothing
python scripts/build.py examples/multi-brand-sample.yaml --approve --out ds-out
```

`--approve` is the sign-off gate. A failing contrast pair blocks export (exit 1). Output depends only on the config.

## What it generates

| Output | Notes |
| --- | --- |
| `decision-brief.md`, `ds.config.yaml` | the signed-off decisions and the config to rerun |
| `contrast-matrix.md/.csv` | every text and UI pair in every mode, with suggested fixes |
| `figma-build/*.js` | `use_figma` scripts: Primitives, Device, Brand (or Theme), text styles. Verified path |
| `figma/*.tokens.json` | native variable JSON, one file per collection and mode. **Not yet validated** against a real Figma export |
| `dtcg/` | DTCG tokens per mode plus a Style Dictionary config |
| `build-plan.md` | phases with human checkpoints for `figma-generate-library` |
| `decision-records/` | one record per key decision |

## Rules worth knowing

- **Contrast wins over anchor fidelity.** The exact brand hex is always kept as a token; it lands on a ramp step only if that step still passes. Otherwise the ramp is calibrated and the anchor is flagged with the text color that works on it.
- **Contrast target is selectable:** `AA` (4.5 / 3), `AAA` (7 / 4.5) or custom ratios.
- **Brands are modes, never collections.** Semantic tokens are aliases only.
- **Indicator versus action split:** the fill can be light, but focus rings and selection marks use a darker step that meets 3:1.

## Status (v0.2.0, see [CHANGELOG](CHANGELOG.md))

Generated and tested: primitives, device and brand/theme collections, contrast matrix, Figma build scripts, build plan, decision brief and records, DTCG. 74 tests; the multi-brand sample reproduces the structure of the real Multi-Brand DS Figma file (same collections, modes and variable names) with 0 failing pairs.

Built-in dimensions: `brand`, `theme`, `device`, `platform`, `density`, `a11y`, `context`, `locale`, combinable, plus your own through `custom_dimensions`. Layering (for example brand under theme) is automatic. Not generated: per-script line heights, and anything that needs math between modes, because Figma variables have none.

```bash
python -m unittest discover -s tests -v
```
