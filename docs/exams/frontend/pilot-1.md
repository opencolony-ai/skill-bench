# Front-end exam, pilot 1 (2026-11-14)

Exam v1 as registered in [design.md](design.md): 13 items (3 practice, 10 scored), layers 1–2 and the
item-type checks graded by `graders/web/`. Claude Code with Sonnet, files only, each item in its own session.
Layers 3–5 (the judge and sameness) were not run in this pilot.

| Arm | Items where Claude opened the skill | Checks passed | Items with no breakage | Tokens |
| --- | --- | --- | --- | --- |
| no skill, run 1 | – | 195/204 (96%) | 9/10 | 1.9M |
| no skill, run 2 | – | 193/204 (95%) | 8/10 | 1.9M |
| frontend-design, installed | 1/13 | 192/204 (94%) | 8/10 | 1.9M |
| placebo, installed | 1/13 | 191/204 (94%) | 9/10 | 2.0M |
| frontend-design reversed, installed | 1/13 | 190/204 (93%) | 8/10 | 1.9M |
| frontend-design, named | 13/13 | 191/204 (94%) | 7/10 | 2.1M |
| placebo, named | 13/13 | 193/204 (95%) | 10/10 | 2.0M |
| frontend-design reversed, named | 13/13 | 194/204 (95%) | 8/10 | 2.0M |

## What it shows

1. **The exam is far too easy for Sonnet.** Without a skill it passes 95% of the checks; the registered target
   was 20–60%. Every arm is within the run-to-run spread of the no-skill arm (95–96%).
2. **The validity checks fail, for a reason worth knowing.** The reversed skill (fixed 1,100 px width, no focus
   outlines, `transition: all`, cream and terracotta, "Oops" errors) was loaded on all 13 items in the named arm,
   and Claude followed almost none of it: none of those traits appear in its pages. The only reversed rule it
   followed is all-caps labels (5 of 7 built pages, against 1 without a skill), a style rule the exam
   deliberately does not score. When a skill's advice conflicts with the brief (works on a phone, accessible),
   Sonnet follows the brief. So skills, good or bad, barely move layers 1–2 for Sonnet: what they change is style.
3. **Installed skills are rarely opened.** With the skill installed and the task not naming it, Claude opened
   frontend-design (Anthropic's most installed front-end skill) on 1 of 13 front-end tasks.
4. **The review decoys were not clean.** Claude's reviews were thorough and named real problems on the decoy
   lines (a table without a caption, an unhandled promise rejection), and cited line ranges that covered them.
   A decoy must be wrong in one respect only, and count only when the review calls that respect wrong.

## Changes before pilot 2

- Decoys rebuilt: a decoy line is correct in every respect, and a citation counts as flagging it only when it
  names the decoy's trait (`flag_words`); findings likewise need their trait named.
- Harder layer 1–2 floor where the skills agree and a brief can fairly ask for it (44 px targets on phones,
  16 px inputs, no hover-only controls, no `100vh` heroes), stated in the briefs.
- Run Haiku, where the floor is not yet met, to see whether skills matter more for a weaker model.
- Run layers 3–5 (first-screen test, blind pairwise, sameness): the only layers that can see a style effect.
- The per-item record of whether the skill was opened is now kept in every result.
