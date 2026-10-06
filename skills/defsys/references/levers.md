# Essence to levers

A starting suggestion, never a verdict. The designer accepts, edits or rejects each lever. Same data as `scripts/levers.py`, which the decision brief uses.

Evidence ladder for any recommendation, strongest first: **standard** (WCAG, platform guideline) > **convention** (what users expect) > **system logic** (what keeps the system consistent) > **brand intent** (what the brand said) > **taste**. Say which rung you are on.

| Word | Color coverage | Type character | Shape | Density | Elevation |
| --- | --- | --- | --- | --- | --- |
| premium | restrained: neutrals carry the page, brand color rare and deep | lighter weights, refined serif or neo-grotesque | small radii, crisp | spacious | subtle, soft shadows |
| playful | high coverage, saturated, warm neutrals | rounded humanist, heavy headings | large radii, pill buttons | comfortable | flat with color blocking |
| energetic | high saturation, bold contrast | heavy weights, tight heading leading | medium to large radii | compact to comfortable | flat, sharp offsets |
| cheerful | warm light brand color used generously, dark text on it | friendly rounded sans, medium body | large radii | comfortable | flat |
| trustworthy | cool blues and greens, neutral-dominant | neutral sans, regular weights | medium radii | comfortable | subtle |
| calm | low saturation, wide neutral range | light to regular, open leading | medium to large radii | spacious | very soft |
| bold | full-strength brand color, strong darks | heavy headings, large scale | sharp or pill, never mid | comfortable | flat or hard shadow |
| minimal | near-monochrome, one accent | one family, few weights | small radii | spacious | none |
| friendly | warm accents, soft neutrals | rounded or humanist sans | large radii | comfortable | soft |
| technical | cool neutrals, status colors prominent | grotesque plus mono for data | small radii | compact | borders over shadows |
| warm | warm neutrals, earthy brand color | humanist or serif headings | medium radii | comfortable | soft |
| snackable | bright, high coverage | short heavy headings, rounded sans | large radii | compact | flat |

Mapping to config: shape -> `radius: {button, field, card, control}` (px or `full`); type -> `fonts`, `weights`; density -> `density: default|roomy`; color coverage -> which anchors exist and which is `primary`; neutral temperature -> `neutral: warm|cool`. Elevation is recorded in the brief; v1 does not generate shadow tokens.
