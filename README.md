# skill-bench

**Does a skill actually make Claude better at the work it is for?** Most skills are never measured.
skill-bench measures each one the same way, many times, by different people: Claude Code does the
skill's small test cases twice, once without the skill and once with it, and a program grades the
files it writes. A result counts when three people other than the skill's author get the same answer.

See the [leaderboard](LEADERBOARD.md).

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
  skill from here leaks in. Claude may only read and write files there: no shell, no web.
- One verification is two Claude Code runs. Measured on `conventional-commit` (3 cases, Sonnet):
  about 35 seconds and US$0.29 at API prices; on a subscription it uses your plan's allowance.
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
- Changing a skill or any of its cases gives it a new version; results for older versions stop counting.

## Add a skill

A skill is a folder under `skills/`:

```
skills/<name>/SKILL.md          the skill, in the Agent Skills format
skills/<name>/skill.json        {"author": "<your-github-name>"}
skills/<name>/cases/<case>/task.md        what Claude is asked to do
skills/<name>/cases/<case>/...            input files
skills/<name>/cases/<case>/_bench/expect.json   which check, and what it expects (Claude never sees _bench/)
skills/<name>/cases/<case>/_bench/ref*/         answers that must pass (more than one form is better)
skills/<name>/cases/<case>/_bench/trivial*/     answers that must fail
```

- Write at least three cases. Good cases are small, need what the skill teaches, and are graded by a program.
- `python bench.py check-cases` must pass: every `ref*` answer passes and every `trivial*` answer fails.
- Checks live in `checks.py`. A new kind of check is a pull request to that file.
- `commit-tips` is a deliberately vague control skill that reuses the `conventional-commit` cases: it shows what "no effect" looks like.

## Where this comes from

skill-bench grew out of [OpenColony](https://github.com/opencolony-ai), a file-based way for people and their
agents to work on one plan. A small pilot (five skills, three independent verifiers) found that the verifiers
agreed on every skill that had an effect, and that the same cases tell a useful skill from a vague one.

License: MIT.
