# skill-bench

**Does a skill actually make Claude better at the work it is for?** Most skills are never measured.
skill-bench measures each one the same way, many times, by different people: Claude Code does the
skill's small test cases twice, once without the skill and once with it, and a program grades the
files it writes. A result counts when three people other than the skill's author get the same answer.

See the [colony dashboard](https://opencolony-ai.github.io/skill-bench/colony.html) (every skill, who verified
it, points), the [report](https://opencolony-ai.github.io/skill-bench/) (what Claude wrote, side by side) and the
[leaderboard](LEADERBOARD.md). All three are built from `results/`; the dashboard reads one file,
[`colony.json`](https://opencolony-ai.github.io/skill-bench/colony.json), which any other site can read too
(`colony.html?data=<url of colony.json>`).

Skills are grouped into colonies, one per use, in `colonies.json`. Points are computed from `results/` only
(`report.points`): +1 for every verification CI accepted, +1 for being among the first three verifiers of a
skill version, +2 when at least three people have verified that version and your run agrees with the median
within one case. Points cannot be transferred; they are a public record of the work.

## Reading a result

Every skill gets one card:

```
writing-plans                 without the skill → with it
  Results            3/3 → 3/3        did what the task asked
  Follows the skill  0/3 → 3/3        kept the rules the skill states
  Tokens             147k → 203k (+38%)
  Time               50 s → 82 s
  Verdict: Same results, follows the skill's format, uses 38% more tokens.
```

Below it, every case side by side: the page Claude built (in a frame that runs no script) or the text it
wrote, with what a failed rule points at highlighted, and every check ticked or crossed in plain words.

**The bar.** Each check is one of two kinds, fixed in the repository before anyone runs:

- **Result**: something the task itself asks for, so Claude without the skill has a fair chance at it.
  It must not depend on format ("L3", "line 3" and "第 3 行" all count).
- **Rule**: something the skill tells Claude to do. It quotes the skill's own sentence, and the tests fail if
  the quote is not in the skill. A rule the skill does not state cannot be checked.

The verdict follows fixed rules: results first (better / worse), then format ("same results, follows the
skill's format"), then tokens used. Following the skill's rules is not counted as doing better: without the skill,
Claude was never told them.

## Verify a skill (about 5 minutes)

You need Python 3.10+, [Claude Code](https://code.claude.com) signed in, and a fork of this repository.

```bash
python bench.py next --user <your-github-name>
```

```bash
python bench.py run <skill>
```

```bash
python bench.py submit <the folder it printed> --user <your-github-name>
```

Then open a pull request with the one file it wrote under `results/`. CI checks it and a maintainer merges it.

- `next` picks the skill for you. You cannot pick, and you never get your own skill or one you already verified.
- `run` does everything in your system's temp folder, outside this repository, so no `CLAUDE.md` or
  skill from here leaks in. Your own skills, plugins and MCP servers stay out too (Claude Code runs without
  your user settings), so both runs see only Claude Code's built-in skills, plus the one being measured.
  Claude may only read and write files there: no shell, no web.
- Each result records which tools Claude called and whether it opened the skill at all. A skill that
  Claude never opens cannot help, and the leaderboard says how often that happened.
- One verification is two Claude Code runs. Measured on `conventional-commit` (3 cases, Sonnet):
  about 1–2 minutes and a few hundred thousand tokens (mostly Claude Code's own prompt, read from cache) of your
  subscription's allowance: no extra money.
- What Claude wrote for each case goes into the result, so anyone can re-grade it. Test cases are public.

## How results are judged

| Status | Meaning |
| --- | --- |
| ✅ consistent | At least 3 people other than the author ran it, and each one's pass count is within 1 case of the median, with and without the skill |
| ⚠️ disputed | They disagree. More people are asked |
| ➖ no signal | Claude already passes these cases without the skill, so they cannot show what the skill adds |
| 🕓 self-reported | Fewer than 3 people so far |

- **The model is not verified.** Each result records what Claude Code reported, but nobody can prove it. Agreement
  between independent people is the safeguard.
- Results are re-graded in CI from the files Claude wrote, using the checks on the main branch, never the ones in the pull request.
- A run that the environment stopped (for example a refused permission) is recorded as "could not run", not as a failure.
- Changing a skill (any file in its folder), any of its cases or its checker gives it a new version; results for
  older versions stop counting.

## Shared exams

Skills that do the same kind of work take the same exam, so they can be compared with each other: a skill
says so with `"exam": "<colony>"` in its `skill.json`. The front-end exam (`docs/exams/frontend/`) has three
public practice items in `exams/frontend/practice/` and ten scored items kept in a private repository
(`SKILL_BENCH_EXAMS=<path to it> python bench.py run <skill>`), each run in its own Claude Code session and
graded by `graders/web/` in headless Chromium (Node 22 and `npm ci --prefix graders/web`). Skills that run only
when called by name are measured with a third arm, `--arms none,skill,named`, where the task says to use the skill.

## Add a skill

A skill is a folder under `skills/`:

```
skills/<name>/SKILL.md          the skill, in the Agent Skills format
skills/<name>/skill.json        {"author": "<your-github-name>"}, plus "source" and "license" for a skill you did not write
skills/<name>/cases/check.py              optional: this skill's own checker (expect.json then says "check": "script")
skills/<name>/cases/<case>/task.md        what Claude is asked to do
skills/<name>/cases/<case>/...            input files
skills/<name>/cases/<case>/_bench/expect.json   which check, and what it expects (Claude never sees _bench/)
skills/<name>/cases/<case>/_bench/ref*/         answers that must pass (more than one form is better)
skills/<name>/cases/<case>/_bench/trivial*/     answers that must fail
```

- Write at least three cases. Good cases are small, need what the skill teaches, and are graded by a program.
- `python bench.py check-cases` must pass: every `ref*` answer passes and every `trivial*` answer fails.
- Checks live in `checks.py`, or in the skill's own `cases/check.py`: `check(folder, expect)` returns
  `{check name: passed}`, and `ABOUT` says what each check is (kind, plain words in English and Chinese,
  the quoted sentence for a rule, optionally a pattern to highlight when it fails). It reads the files
  Claude wrote and never runs them. An imported skill needs at least one result check. Either one is reviewed like code,
  and results are always re-graded with the copy on the main branch.
- A skill you did not write keeps its author, its source (repository and commit) and its licence file. Its author
  is the upstream owner, who therefore cannot verify it.
- `commit-tips` is a deliberately vague control skill that reuses the `conventional-commit` cases: it shows what "no effect" looks like.

## Where this comes from

skill-bench grew out of [OpenColony](https://github.com/opencolony-ai), a file-based way for people and their
agents to work on one plan. A small pilot (five skills, three independent verifiers) found that the verifiers
agreed on every skill that had an effect, and that the same cases tell a useful skill from a vague one.

License: MIT.
