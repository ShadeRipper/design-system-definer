# Discovery interview

One question at a time. Each question: the question, a one-line *why this matters*, an example answer. Skip any the designer already answered (Express mode, pasted brand guide). Save to `ds.config.yaml` after each stage.

Open by asking: Guided or Express? First design system, or experienced? Then run the stages.

## 1. Context

| Ask | Why | Example |
| --- | --- | --- |
| What kind of system is this? (single brand; single brand light/dark; multi-brand or white-label; house of brands; multi-platform; responsive; product plus marketing; accessibility variants; multi-locale; custom) | The type decides the collections and modes, which are the one thing that is expensive to change later | "Three snack brands on one core" |
| What are you building, for whom, on which platforms? | Sets density, touch targets and the device dimension | "Account sign-up on iOS, Android and web" |
| How many brands (or themes)? | Brands become modes of one collection | "Three, plus a neutral base" |
| What do you already have: logo, colors, fonts, brand guide? | Anything supplied skips later questions | "Hex for yellow and red, Nunito" |

Follow-up: if multi-brand, defer the Base-mode question to stage 4.

## 2. Brand essence (per brand)

| Ask | Why | Example |
| --- | --- | --- |
| Three words for how this brand should feel. | Words become concrete levers in stage 3; without them color is picked by eye | "cheerful, playful, snackable" |
| One thing it must never feel like. | The exclusion catches contradictions faster than the adjectives | "corporate" |

**Challenge vague words.** "Premium": restraint and whitespace, or rich materials and depth? "Modern": what is the brand reacting against? "Friendly": warm and rounded, or simple and approachable? "Bold": loud color, or heavy type, or both?

## 3. Lever mapping

For each word, propose from [levers.md](levers.md) how it lands on five levers: **color coverage**, **type character**, **shape**, **density**, **elevation**. Show the reasoning rung (standard, convention, system logic, brand intent, taste). Ask accept / edit / reject per lever. Record accepted levers as config: `radius`, `weights`, `fonts`, `density`.

Flag contradictions: "cheerful" plus "corporate" excluded is consistent; "playful" plus tiny sharp radii is not: ask which wins.

## 4. Variation

Ask what varies **independently** and walk the list: brand, light/dark, device, platform (web, iOS, Android), density, accessibility (large text, reduced motion), locale or script, product versus marketing type. Two things that always change together are one dimension. Derive one collection per dimension and show the mode table ([system-types.md](system-types.md)). Anything off the list becomes a `custom_dimensions` entry; ask what its modes are and which existing token each mode should use.

Questions per dimension: *platform*: which platforms, and do you follow Apple 44pt and Material 48dp touch targets? *density*: which densities, and where do they differ (padding, gaps)? *a11y*: large text and reduced motion as modes? *locale*: which scripts, and are any right-to-left? *house of brands*: which brand is the master, and what does each sub-brand override?

Multi-brand only: **Base mode?** Include it for white-label systems (the brand is unknown until runtime) and when components need a default look in docs and tests; omit it when every product always ships with a known brand. Set `base_mode: include` or `none`.

## 5. Anchors

| Ask | Why | Example |
| --- | --- | --- |
| Brand colors as hex, with a name for each (yellow, red). | Ramps are built from them; names become token names | `yellow: "#FFC72C"` |
| Which one drives primary actions? | Sets `primary` | "yellow" |
| Fonts per brand for headings and body. | Fonts are often proprietary; the type system binds to the family | "Nunito for both" |
| Neutral temperature per brand (warm, cool). | Neutrals carry most of the interface | "warm" |

Check each anchor before moving on: a light brand color (like yellow) cannot carry white text and cannot be a 3:1 focus ring on white. Say so now; the skill pairs it with dark text and uses a darker step as the indicator. If fonts are proprietary, offer open substitutes and record the choice.

## 6. Constraints

| Ask | Why | Example |
| --- | --- | --- |
| Contrast target: AA (4.5 text, 3 UI), AAA (7 / 4.5) or custom? | Every pair is checked against it in every mode | "AA" |
| Minimum touch target? | Sets control height | "48px" |
| Spacing base unit? | One grid for all gaps | "4px" |
| Locales or scripts beyond Latin? | Type families and line heights may need to change | "English only" |

Component-token tier defaults to `minimal` (control height, icon size, special radii decided now). Mention it; change only if asked.

## 7. Playback

Run `python scripts/build.py ds.config.yaml` (no flags). Present the printed decision brief: every decision with its reason. Do not generate files until the designer approves it explicitly. Changes: edit the config and re-run.
