# The front-end exam (v1 design, registered before any run)

One exam for every front-end skill, so skills in the colony can be compared. This file is the bar: what is
asked, how it is scored and what counts as an effect are fixed here before the pilot, and a change gives the
exam a new version. Evidence: [CLAIMS.md](CLAIMS.md) (what 26 testable skills promise) and
[prior-art.md](prior-art.md) (what other benchmarks do and where they fall short).

## What is measured

Whether a skill makes Claude Code produce front-end work that is **less broken, closer to the brief, easier
to understand and preferred by people**, and at what cost in tokens and time. Only claims many skills share
are scored (CLAIMS.md); claims they disagree on are never scored by the exam.

## Arms

| Arm | What Claude has | Answers |
| --- | --- | --- |
| none | Claude Code alone | the baseline |
| auto | the skill installed; Claude decides whether to open it | what installing it does (finding it + using it) |
| named | the skill installed and the task says "use the <skill> skill" | what its content does; the only fair arm for the 9 by-name skills |

Pilot only: **placebo** (a skill of the same length with generic advice) and **sabotaged** (the skill with
its key rules reversed). A sound exam scores placebo ≈ none and sabotaged < the real skill.

Runs are tier 0: Claude reads and writes files only, no shell, no web, no image tool, in both arms. Rendering
and all measuring happen afterwards on the grader's machine. Skills that render their own work (ui-taste,
impeccable, design-taste-frontend) are therefore judged on their guidance alone; a tier 2 variant is later work.

## Items

Ten scored items, kept private and rotated, and three public practice items of the same kinds.

| Item type | Scored items | What makes it hard |
| --- | --- | --- |
| Build from a brief | 3 | real, dense, bilingual content; conflicting constraints (a brand palette that fails contrast); 320 px; users with low vision |
| Improve an existing page | 1 | planted faults to fix, behaviour that must keep working (hidden tests) |
| Survive worst-case data | 2 | the page reads `data.js`; hidden fixtures swap in empty, one, 1,000 rows, unbreakable names, missing fields, right-to-left text, an error flag |
| Add motion | 1 | the grader opens each control: durations, easing, animated properties, origin, reduced motion; a command palette and tab switch that must not animate (traps) |
| Review code | 2 | planted faults and decoys that look wrong but are right; findings must name file:line; source files must not change |
| Rebuild a screenshot | 1 | the reference's layout, text and colours, built from real text and controls |

Every brief names the subject, audience and job, answers the questions a skill might stop to ask, and says
the output is self-contained (no network at grading).

## Five layers

| Layer | Question | How | Kind |
| --- | --- | --- | --- |
| 1 Breaks | Does it break? | `graders/web/render.cjs` at 320 / 768 / 1280 px, offline: sideways scroll, text past the edge, clipped or overlapping text, tap targets < 24 px, text < 12 px, line length, axe-core serious/critical, visible keyboard focus, motion under reduced motion, network requests, script errors | program |
| 2 Brief | Did it do what the brief asked? | per-item checklist: DOM checks where possible (required text, controls, states under fixtures, no source edits), yes/no judge questions otherwise | program + judge |
| 3 Understood | Does a viewer get it? | the judge sees only the first screen (or, for reviews, only the findings) and answers the item's questions; answers are compared with the brief's | judge, answer known |
| 4 Preferred | Which is better for this brief? | blind pairwise, both orders, screenshots at two widths plus the code; people (verifiers vote on other people's pairs) and the judge; Bradley–Terry with bootstrap intervals grouped by item | people + judge |
| 5 Sameness | Is it templated? | similarity of one skill's pages across different briefs, and to the no-skill pages: computed fonts, palette, layout skeleton, screenshot hash | program |

The judge is Claude (a pinned Opus or Fable model, recorded with every judgement) run on the maintainer's
schedule; a model change starts a new judge version. Before layer 3 or 4 counts, the judge is checked against
people on a labelled set (target κ ≥ 0.6, reported with the people's own agreement) and against known answers
(a page degraded on purpose must lose).

Prior art says a judge is near chance when two pages are close in quality, which is exactly a skill's small
effect. So layers 1–3 carry the verdict, and layer 4 needs many votes: about 85 non-tie votes to see a 65%
win rate, about 200 for 60% (prior-art.md §6).

## What counts as an effect

Per item, an arm **passes layer 1** with no sideways scroll at 320 px, no overlapping or clipped text, no
axe-core serious or critical issue, focus visible on every tabbed control, nothing endless under reduced
motion, no network request and no script error. Layer 2 is the share of checklist items met; layer 3 the
share of questions answered as the brief says.

The skill's card shows, without and with the skill: layer 1 pass rate, layer 2 and 3 shares, layer 4 win rate
with its interval, layer 5 sameness, tokens and time. The verdict follows the leaderboard's fixed rules: results
(layers 1–3) first, then format, then tokens. Layer 4 is shown, and enters the verdict only once its interval
excludes 50%.

## Difficulty

Target: without a skill, Claude Sonnet passes 20–60% of what each item checks, and no arm aces the exam. The
pilot measures every item's difficulty and discrimination; an item everyone passes or everyone fails is
replaced before v1 is frozen.

## Pilot

Sonnet and Haiku; arms none, auto, named; skills frontend-design, emil-design-eng, design-taste-frontend-v1
(by name), ui-ux-pro-max; plus placebo and sabotaged frontend-design. Report: per-item difficulty, the three
validity checks (placebo ≈ none, sabotaged < real, Sonnet > Haiku without a skill), run-to-run spread, tokens.
