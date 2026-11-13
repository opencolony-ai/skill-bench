# What front-end skills claim

Read on 2026-11-13: 115 candidates (`candidates/frontend-review.json`) from the skills.sh leaderboard and the
Claude plugin directory, each SKILL.md and the files it points to read in full. Every claim below is quoted
from a skill's own text (the quotes were checked word for word against the source).

- **34 are front-end skills**; 26 of them can be tested on our tiers (0 files only, 1 offline commands,
  2 a browser). 5 need a paid service, an account or the Figma MCP (`out`); 1 is a retired stub.
- **9 run only when called by name** (`disable-model-invocation`, or "runs only when called by name"), so
  the exam has a third arm that names the skill.
- Others: video (Remotion, HyperFrames), Figma-only, deployment and planning skills turned up by the
  keyword search; they are listed with the reason in `candidates/frontend-review.json`.

## Claims shared by many skills: the shared exam scores these

Counted over the 26 testable skills, by keywords over their claims (rough; the exact claims are in the JSON).

| Claims | Skills | Scored by |
| --- | --- | --- |
| Accessibility floor: 4.5:1 contrast, visible keyboard focus, labelled controls, real buttons and links | 13 | layer 1 (axe-core, focus test) |
| Motion restraint: no animation on keyboard-driven or 100+/day actions; one orchestrated moment, not every section | 11 | motion item (driven interactions) |
| Works on a phone: nothing past the edge at 320 px, one column, `dvh`, targets ≥ 24–44 px, inputs ≥ 16 px, zoom kept | 10 | layer 1 |
| Reduced motion respected | 10 | layer 1, motion item |
| Typography: one or two families, body measure ≤ 75–80 ch | 10 | layer 1 (line length), layer 2 |
| Avoid the "AI default" look: purple glow, glass cards, emoji as icons, template sections | 9 | layer 5 (sameness), layer 4 (pairwise) |
| Easing and duration: ease-out, never ease-in, UI motion under 300 ms | 8 | motion item |
| Loading, empty, error, one / many / huge states | 8 | states items (hidden data fixtures) |
| Entrances never from `scale(0)`; press feedback around 0.97 | 7 | motion item |
| Copy: buttons name the action, errors say how to fix, real content (no lorem, no John Doe) | 7 | layer 2, layer 3 |
| Animate only `transform` and `opacity`; no `transition: all` | 6 | motion item |
| Reviews: one finding per line with file:line, no source edits, decoys left alone | 6 | review items |
| One system: one accent, one radius scale | 4 | not scored (style) |
| React structure and performance | 4 | not in v1 (needs a React project, tier 1) |
| Render and report honestly what was checked | 3 | not in v1 (the run is tier 0) |
| Gestures (springs, velocity, rubber-band), variants, matching a reference image | 2–3 each | one reference item; gestures and variants not in v1 |

## Claims the skills disagree on: never scored by the shared exam

| Topic | One side | Other side |
| --- | --- | --- |
| All-caps labels and eyebrow labels above headings | frontend-design, ui-taste, impeccable: a template tell | minimalist-ui (uppercase pill tags), industrial-brutalist-ui (all-caps), high-end-visual-design (eyebrow pills) |
| Scroll-triggered entrances | frontend-design, design-taste-frontend: not on every section | high-end-visual-design: on every element; design-taste-frontend-v1: endless motion by default |
| Hover motion | frontend-design: not on every card | design-taste-frontend: on every linked card |
| Case of headings and buttons | frontend-design: sentence case | web-design-guidelines: Title Case |
| Fonts | several ban Inter, Roboto, Open Sans | no skill requires them; a font choice is style, not quality |
| Gradients, shadows, corner radius | each style skill fixes its own | — |

These still show on each skill's own card as "follows the skill" (rules quoted from that skill), never as the
exam's result.

## What the skills produce (the exam has one item type for each)

| Output | Skills |
| --- | --- |
| A new page or screen from a brief | frontend-design (2 copies), design-taste-frontend (+ v1), ui-taste, uizze-ui, ui-ux-pro-max, high-end, minimalist, brutalist, gpt-taste, emil-design-eng, mobile-native, apple-design |
| An improved existing page that keeps working | impeccable, uizze-ui, ui-taste, emil-design-eng |
| Components that survive worst-case data | break-ui, ui-taste, design-taste-frontend-v1, uizze-ui |
| Motion added to an interface | animate, emil-design-eng, apple-design, find-animation-opportunities |
| A review or audit, not code | review-animations, improve-animations, find-animation-opportunities, web-design-guidelines, break-ui |
| A page rebuilt from a reference screenshot | image-to-ui, uizze-ui |
| React structure and performance | vercel-react-best-practices (2 copies), vercel-composition-patterns (v2) |

## Fairness notes from the reading

- Five Emil Kowalski skills answer a bare invocation with a fixed greeting: every item states the task.
- frontend-design may stop to confirm the subject, impeccable asks 2–3 questions, brainstorming fires on any
  creative work: every brief names the subject, audience and job, and says the answers to such questions.
- ui-taste and uizze-ui generate an image first when an image tool exists: both arms get the same tools (none).
- web-design-guidelines downloads its rules on every run (tier out); a pinned copy would make it tier 0.
- design-taste-frontend makes random choices, so it varies more between runs: the median over verifiers handles it.
