#!/usr/bin/env python3
"""skill-bench: does a skill make Claude better at the work it is for? Measured by many people,
each on their own Claude Code, counted when independent runs agree.

    python bench.py list                       skills and how far each is verified
    python bench.py next --user <github-name>  the skill to verify next (chosen for you)
    python bench.py run <skill>                run it with and without the skill, grade both
    python bench.py submit <run-folder>        write the result into results/ for a pull request
    python bench.py board                      rebuild LEADERBOARD.md from results/
    python bench.py site                       build the report (site/): what Claude wrote, side by side

    python bench.py check-cases                every case: its reference passes, its trivial answer fails
    python bench.py verify <result.json>...    what CI runs on a pull request (re-grades the outputs)

Only the Python standard library and the `claude` command (Claude Code) are needed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import checks

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
RESULTS = ROOT / "results"
SCHEMA = 1
NEED = 3          # independent verifiers before a result counts
TOLERANCE = 1     # a verifier agrees when each arm is within this many cases of the median
ARMS = ("none", "skill")
PROMPT = ("Do each task in the case-* folders of the current folder: read its task.md and do what it asks, "
          "writing your outputs inside that same case folder. Work only inside the current folder. "
          "Do not use the internet.")


class BenchError(Exception):
    pass


# ------------------------------------------------------------------ skills and cases

def skill_meta(name: str) -> dict:
    d = SKILLS / name
    if not (d / "SKILL.md").is_file():
        raise BenchError(f"no skill {name!r} (see `python bench.py list`)")
    meta = json.loads((d / "skill.json").read_text(encoding="utf-8")) if (d / "skill.json").is_file() else {}
    meta.setdefault("author", "")
    meta.setdefault("cases_from", name)
    return meta


def skill_names() -> list[str]:
    return sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))


def case_dirs(name: str) -> list[Path]:
    src = SKILLS / skill_meta(name)["cases_from"] / "cases"
    return sorted(p for p in src.iterdir() if p.is_dir() and (p / "task.md").is_file()) if src.is_dir() else []


def _files(d: Path) -> list[Path]:
    return sorted(p for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def version(name: str) -> str:
    """Changes when the skill (any of its files), its cases or its case checker changes: results for an
    older version stop counting."""
    h = hashlib.sha256()
    d = SKILLS / name
    own = [q for q in _files(d) if q.name != "skill.json" and "cases" not in q.relative_to(d).parts]
    src = SKILLS / skill_meta(name)["cases_from"] / "cases"
    for p in own + [q for c in case_dirs(name) for q in _files(c)] + [q for q in [src / "check.py"] if q.is_file()]:
        h.update(str(p.relative_to(SKILLS)).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:12]


def expect_of(case: Path) -> dict:
    e = json.loads((case / "_bench" / "expect.json").read_text(encoding="utf-8"))
    if e.get("check") == "script":  # the skill's own checker, cases/check.py, reviewed like checks.py
        e["_script"] = str(case.parent / "check.py")
    return e


def copy_inputs(case: Path, dest: Path) -> None:
    """What the agent may see: everything in the case folder except _bench/."""
    for p in case.iterdir():
        if p.name == "_bench":
            continue
        (shutil.copytree if p.is_dir() else shutil.copy2)(p, dest / p.name)


# ------------------------------------------------------------------ results

def load_results(name: str | None = None) -> list[dict]:
    out = []
    for f in sorted(RESULTS.glob("*/*/*.json")):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if name is None or r.get("skill") == name:
            r["_file"] = str(f)
            out.append(r)
    return out


def passes(r: dict, arm: str) -> int | None:
    a = r.get("arms", {}).get(arm) or {}
    if a.get("could_not_run"):
        return None
    return sum(1 for c in (a.get("cases") or {}).values() if c.get("pass"))


def _abouts(name: str) -> dict:
    return {c.name: checks.about(expect_of(c)) for c in case_dirs(name)}


def split(r: dict, arm: str, abouts: dict) -> dict:
    """One arm of one result, told apart: cases whose result checks all pass, cases whose rule checks
    all pass (None when the cases check no rule), and what the arm used."""
    a = (r.get("arms") or {}).get(arm) or {}
    res = rule = 0
    has_rule = False
    for cn, c in (a.get("cases") or {}).items():
        kinds = abouts.get(cn, {})
        got = c.get("checks") or {}
        res += all(v for k, v in got.items() if kinds.get(k, {}).get("kind", "result") == "result")
        rules = [v for k, v in got.items() if kinds.get(k, {}).get("kind") == "rule"]
        has_rule |= bool(rules)
        rule += all(rules)
    u = a.get("usage") or {}
    return {"result": res, "rule": rule if has_rule else None, "cost": u.get("cost_usd"), "tokens": u.get("total_tokens"),
            "seconds": (u.get("duration_ms") or 0) / 1000 or None, "output_tokens": u.get("output_tokens")}


def _median(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return statistics.median(xs) if xs else None


def verdict(s: dict) -> tuple[str, float | None]:
    """The one-line reading of a standing, by fixed rules: results first, then format, then tokens.
    Returns (better | worse | format | none, change in tokens used, in percent). Tokens, not money:
    verifiers run on their own Claude subscription, where a run costs allowance, not dollars."""
    pct = None
    if s.get("tokens_none") and s.get("tokens_skill") is not None:
        pct = round((s["tokens_skill"] - s["tokens_none"]) / s["tokens_none"] * 100)
    if s["result_skill"] > s["result_none"]:
        return "better", pct
    if s["result_skill"] < s["result_none"]:
        return "worse", pct
    if s.get("rule_skill") is not None and s["rule_skill"] > (s.get("rule_none") or 0):
        return "format", pct
    return "none", pct


def standing(name: str) -> dict:
    """Where a skill stands for its current version: self-reported, consistent, disputed, no signal."""
    meta, ver, n = skill_meta(name), version(name), len(case_dirs(name))
    rs = [r for r in load_results(name) if r.get("version") == ver]
    by_user: dict[str, dict] = {}
    for r in rs:  # one result per person (their latest); the skill's author does not count
        u = str(r.get("user", "")).lower()
        if u and u != meta["author"].lower() and (passes(r, "none") is not None and passes(r, "skill") is not None):
            if u not in by_user or r.get("finished", "") > by_user[u].get("finished", ""):
                by_user[u] = r
    runs = list(by_user.values())
    out = {"skill": name, "version": ver, "cases": n, "verifiers": len(runs), "users": sorted(by_user),
           "stale": len([r for r in load_results(name) if r.get("version") != ver])}
    if not runs:
        out["status"] = "not yet run"
        return out
    a = [passes(r, "none") for r in runs]
    b = [passes(r, "skill") for r in runs]
    ma, mb = statistics.median(a), statistics.median(b)
    out.update(none_median=ma, skill_median=mb, effect=mb - ma, none_passes=a, skill_passes=b)
    toks = [r.get("arms", {}).get("skill", {}).get("usage", {}).get("total_tokens") for r in runs]
    toks = [t for t in toks if isinstance(t, (int, float))]
    out["tokens_median"] = statistics.median(toks) if toks else None
    ab = _abouts(name)
    for arm in ARMS:
        parts = [split(r, arm, ab) for r in runs]
        for k in ("result", "rule", "cost", "tokens", "seconds", "output_tokens"):
            out[f"{k}_{arm}"] = _median([p[k] for p in parts])
    out["verdict"], out["token_change"] = verdict(out)
    used = [r.get("arms", {}).get("skill", {}).get("skill_used") for r in runs]
    out["used"] = sum(1 for u in used if u is True)  # runs in which Claude opened the skill at all
    agree = all(abs(x - ma) <= TOLERANCE for x in a) and all(abs(x - mb) <= TOLERANCE for x in b)
    if len(runs) < NEED:
        out["status"] = "self-reported"
    elif not agree:
        out["status"] = "disputed"
    elif ma >= n:
        out["status"] = "no signal"  # Claude already passes these cases without the skill
    else:
        out["status"] = "consistent"
    return out


# ------------------------------------------------------------------ commands

def cmd_list(_a) -> None:
    for name in skill_names():
        s = standing(name)
        eff = f"{s['none_median']:g}->{s['skill_median']:g} of {s['cases']}" if "effect" in s else "-"
        print(f"{name:24} {s['status']:14} verifiers {s['verifiers']}/{NEED}  {eff}")


def cmd_next(a) -> None:
    user = a.user.strip().lower()
    if not user:
        raise BenchError("give your GitHub user name: python bench.py next --user <name>")
    open_ = []
    for name in skill_names():
        s = standing(name)
        if skill_meta(name)["author"].lower() == user or user in s["users"]:
            continue  # not your own skill, and not one you already verified
        if s["status"] in ("not yet run", "self-reported", "disputed"):
            open_.append((s["verifiers"], name))
    if not open_:
        print("Nothing needs a verifier right now. Thank you!")
        return
    fewest = min(v for v, _ in open_)
    pool = sorted(n for v, n in open_ if v == fewest)
    # chosen for you, not by you: the same person on the same day gets the same skill
    seed = hashlib.sha256(f"{user}|{dt.date.today().isoformat()}|{'|'.join(pool)}".encode()).hexdigest()
    pick = random.Random(seed).choice(pool)
    print(f"{pick}  (version {version(pick)}, {len(case_dirs(pick))} cases)")
    print(f"next: python bench.py run {pick}")


def _usage(js: dict) -> dict:
    u = js.get("usage") or {}
    tot = sum(int(u.get(k) or 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                                             "cache_read_input_tokens"))
    return {"total_tokens": tot, "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
            "cache_write_tokens": u.get("cache_creation_input_tokens"), "cache_read_tokens": u.get("cache_read_input_tokens"),
            "cost_usd": js.get("total_cost_usd"), "turns": js.get("num_turns"),
            "duration_ms": js.get("duration_ms"), "models": sorted((js.get("modelUsage") or {}).keys()),
            "permission_denials": len(js.get("permission_denials") or []),
            "refused": [_refused(d) for d in (js.get("permission_denials") or []) if isinstance(d, dict)]}


def _refused(d: dict) -> str:
    """What Claude Code refused: the tool and where it pointed (a path or pattern), never file contents."""
    i = d.get("tool_input") or {}
    where = next((str(i[k]) for k in ("file_path", "path", "pattern", "notebook_path") if i.get(k)), "")
    return f"{d.get('tool_name', '?')}({where[:160]})" if where else str(d.get("tool_name", "?"))


def _read_stream(text: str) -> tuple[dict, list[dict]]:
    """Claude Code's stream-json: the final `result` event, and every tool call on the way."""
    result, tools = {}, []
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "result":
            result = ev
        elif ev.get("type") == "assistant":
            tools += [c for c in (ev.get("message") or {}).get("content") or []
                      if isinstance(c, dict) and c.get("type") == "tool_use"]
    return result, tools


def _tool_counts(tools: list[dict]) -> dict:
    out = {}
    for t in tools:
        out[t.get("name", "?")] = out.get(t.get("name", "?"), 0) + 1
    return out


def _skill_used(tools: list[dict], name: str) -> bool:
    """Claude invoked the skill, or opened its files: whether it was used at all, not how well."""
    for t in tools:
        i = t.get("input") or {}
        if t.get("name") == "Skill" and str(i.get("skill", "")).split(":")[-1] == name:
            return True
        if f".claude/skills/{name}/" in json.dumps(i):
            return True
    return False


def run_arm(name: str, arm: str, where: Path, model: str, claude: str, timeout: int) -> dict:
    where.mkdir(parents=True)
    for c in case_dirs(name):
        (where / c.name).mkdir()
        copy_inputs(c, where / c.name)
    if arm == "skill":  # Claude Code finds project skills in .claude/skills/<name>/
        dst = where / ".claude" / "skills" / name
        dst.mkdir(parents=True)
        for p in (SKILLS / name).iterdir():
            if p.name not in ("cases", "skill.json"):
                (shutil.copytree if p.is_dir() else shutil.copy2)(p, dst / p.name)
    # Files only: no shell, no web. Both arms work under the same rules, and a skill from a stranger
    # cannot make Claude run commands on the verifier's computer. The verifier's own skills, plugins
    # and MCP servers stay out (user settings are not loaded), so both arms see only Claude Code's
    # built-in skills, plus this skill in the skill arm.
    flags = ["--output-format", "stream-json", "--verbose", "--model", model,
             "--permission-mode", "acceptEdits", "--setting-sources", "project,local",
             "--strict-mcp-config", "--disallowedTools", "Bash", "WebFetch", "WebSearch"]
    # Warm the prompt cache first, with the same setup and a request that touches nothing, so that
    # neither arm pays for writing Claude Code's own prompt into the cache and the other gets it free.
    # Its cost is recorded apart and not counted.
    warm = {}
    try:
        w = subprocess.run([claude, "-p", "Reply with the single word OK. Do not use any tools.", "--max-turns", "1"] + flags,
                           cwd=where, capture_output=True, text=True, timeout=300)
        warm = _usage(_read_stream(w.stdout)[0])
    except (OSError, subprocess.TimeoutExpired):
        pass
    cmd = [claude, "-p", PROMPT, "--max-turns", "60"] + flags
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    try:
        p = subprocess.run(cmd, cwd=where, capture_output=True, text=True, timeout=timeout)
        js, tools = _read_stream(p.stdout)
        ok = p.returncode == 0 and bool(js) and not js.get("is_error")
        err = None if ok else (js.get("result") or p.stderr or f"exit {p.returncode}")[-500:]
    except (OSError, subprocess.TimeoutExpired) as e:
        js, tools, ok, err = {}, [], False, str(e)[-500:]
    out = {"started": started, "usage": _usage(js), "warmup_usage": warm, "tools": _tool_counts(tools),
           "skill_used": _skill_used(tools, name), "cases": grade_arm(name, where)}
    wrote = any(c["outputs"] for c in out["cases"].values())
    if not wrote and (not ok or out["usage"]["permission_denials"]):
        # nothing came of it and the tool refused it something: the environment, not the skill
        out["could_not_run"] = err or (f"{out['usage']['permission_denials']} action(s) refused by Claude Code's permissions: "
                                       + ", ".join(out["usage"]["refused"]))
    elif err:
        out["error"] = err
    return out


def grade_arm(name: str, where: Path) -> dict:
    res = {}
    for c in case_dirs(name):
        got = where / c.name
        r = checks.grade(expect_of(c), got)
        inputs = {p.name for p in c.iterdir() if p.name != "_bench"}
        outputs = {}
        for p in sorted(got.iterdir()) if got.is_dir() else []:
            if p.is_file() and (p.name not in inputs or p.read_bytes() != (c / p.name).read_bytes()):
                try:
                    outputs[p.name] = p.read_text(encoding="utf-8")[:20000]
                except UnicodeDecodeError:
                    outputs[p.name] = None  # not text: not published
        res[c.name] = {"pass": all(r.values()), "checks": r, "outputs": outputs}
    return res


def cmd_run(a) -> None:
    name = a.skill
    meta = skill_meta(name)
    claude = shutil.which(a.claude) or a.claude
    base = Path(a.workdir or tempfile.gettempdir()) / "skill-bench" / \
        f"{name}-{version(name)}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"{name}: {len(case_dirs(name))} cases, two runs (without and with the skill) in {base}")
    arms = {}
    for arm in ARMS:  # outside this repository, so no CLAUDE.md or skill from here leaks in
        print(f"  running: {arm} ...", flush=True)
        arms[arm] = run_arm(name, arm, base / arm, a.model, claude, a.timeout)
        r = arms[arm]
        state = "could not run: " + r["could_not_run"] if r.get("could_not_run") else \
            f"{sum(c['pass'] for c in r['cases'].values())}/{len(r['cases'])} cases pass"
        print(f"  {arm:5} {state}  ({r['usage']['total_tokens']:,} tokens, ${r['usage']['cost_usd'] or 0:.2f})")
    run = {"schema": SCHEMA, "skill": name, "version": version(name), "author": meta["author"],
           "claude_code": _claude_version(claude), "model_requested": a.model, "os": platform.system(),
           "finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "arms": arms}
    (base / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"next: python bench.py submit {base}")


def _claude_version(claude: str) -> str | None:
    try:
        return subprocess.run([claude, "--version"], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _gh_user() -> str | None:
    try:
        p = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True, timeout=30)
        return p.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def cmd_submit(a) -> None:
    run = json.loads((Path(a.run) / "run.json").read_text(encoding="utf-8"))
    user = (a.user or _gh_user() or "").strip()
    if not user:
        raise BenchError("give your GitHub user name: python bench.py submit <run-folder> --user <name>")
    if run["version"] != version(run["skill"]):
        raise BenchError(f"{run['skill']} changed since this run (version {run['version']}, now {version(run['skill'])}); "
                         "run it again")
    run["user"] = user
    stamp = run["finished"].replace(":", "").replace("-", "")[:15]
    dest = RESULTS / run["skill"] / run["version"] / f"{user.lower()}--{stamp}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    rel = dest.relative_to(ROOT)
    print(f"wrote {rel}")
    print("open a pull request with only this file, for example:")
    print(f"  git switch -c result/{run['skill']}-{user.lower()}-{stamp} && git add {rel} && "
          f"git commit -m 'result: {run['skill']} by {user}' && git push -u origin HEAD && gh pr create --fill")


def cmd_check_cases(_a) -> None:
    bad = 0
    for name in skill_names():
        meta = skill_meta(name)
        if meta["cases_from"] != name:
            continue
        for c in case_dirs(name):
            e = expect_of(c)
            answers = sorted(p for p in (c / "_bench").iterdir() if p.is_dir() and p.name.startswith(("ref", "trivial")))
            for need in ("ref", "trivial"):
                if not any(p.name.startswith(need) for p in answers):
                    print(f"BAD {name}/{c.name}: no _bench/{need}/")
                    bad += 1
            for src in answers:  # every ref* must pass, every trivial* must fail
                kind, want = src.name, src.name.startswith("ref")
                with tempfile.TemporaryDirectory() as tmp:
                    copy_inputs(c, Path(tmp))
                    for p in src.iterdir():
                        shutil.copy2(p, Path(tmp) / p.name)
                    r = checks.grade(e, tmp)
                ok = all(r.values()) == want
                bad += not ok
                print(f"{'ok ' if ok else 'BAD'} {name}/{c.name} {kind:7} " +
                      ("" if all(r.values()) else str([k for k, v in r.items() if not v])))
    if bad:
        raise BenchError(f"{bad} case check(s) do not tell a good answer from a bad one")


def cmd_verify(a) -> None:
    """For CI on a pull request. Uses this checkout's skills and checks (the base branch), and only
    the result files from the pull request."""
    author = (a.author or "").lower()
    bad = []
    for f in a.files:
        p = Path(f)
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            bad.append(f"{f}: not readable JSON ({e})")
            continue
        name, problems = r.get("skill"), []
        if r.get("schema") != SCHEMA:
            problems.append(f"schema {r.get('schema')!r}, expected {SCHEMA}")
        if name not in skill_names():
            bad.append(f"{f}: no skill {name!r}")
            continue
        if r.get("version") != version(name):
            problems.append(f"version {r.get('version')} is not the current one ({version(name)}): run it again")
        user = str(r.get("user", "")).lower()
        if author and user != author:
            problems.append(f"result says user {user!r} but the pull request is by {author!r}")
        if user and user == skill_meta(name)["author"].lower():
            problems.append("a skill's author cannot verify their own skill")
        want = Path(f).name.split("--")[0]
        if want != user:
            problems.append(f"file name says {want!r}, result says {user!r}")
        cases = {c.name: c for c in case_dirs(name)}
        for arm in ARMS:
            got = (r.get("arms") or {}).get(arm)
            if not isinstance(got, dict):
                problems.append(f"no {arm} arm")
                continue
            if got.get("could_not_run"):
                continue
            if set((got.get("cases") or {})) != set(cases):
                problems.append(f"{arm}: cases {sorted(got.get('cases') or {})}, expected {sorted(cases)}")
                continue
            for cn, c in cases.items():  # grade again from the outputs, with the checks on main
                with tempfile.TemporaryDirectory() as tmp:
                    copy_inputs(c, Path(tmp))
                    for fn, text in ((got["cases"][cn].get("outputs") or {}).items()):
                        if text is not None and Path(fn).name == fn:
                            (Path(tmp) / fn).write_text(text, encoding="utf-8")
                    regraded = all(checks.grade(expect_of(c), tmp).values())
                if regraded != bool(got["cases"][cn].get("pass")):
                    problems.append(f"{arm}/{cn}: says pass={got['cases'][cn].get('pass')}, re-graded {regraded}")
        bad += [f"{f}: {x}" for x in problems]
        print(f"{'ok ' if not problems else 'BAD'} {f}")
    for b in bad:
        print("  " + b)
    if bad:
        raise BenchError(f"{len(bad)} problem(s)")


STATUS_WORDS = {"consistent": "✅ consistent", "disputed": "⚠️ disputed", "no signal": "➖ no signal",
                "self-reported": "🕓 self-reported", "not yet run": "· not yet run"}


VERDICT_WORDS = {
    "en": {"better": "Better results", "worse": "Worse results", "format": "Same results, follows the skill's format",
           "none": "No effect", "more": "uses {p}% more tokens", "less": "uses {p}% fewer tokens", "same": "about the same tokens"},
    "zh": {"better": "結果變好", "worse": "結果變差", "format": "結果一樣，只改了格式", "none": "沒有效果",
           "more": "多用 {p}% token", "less": "少用 {p}% token", "same": "token 用量差不多"},
}


def ktok(x: float) -> str:
    """Tokens for people: 141k, 1.2M."""
    return f"{x / 1e6:.1f}M" if x >= 1e6 else f"{x / 1e3:.0f}k"


def verdict_text(s: dict, lang: str = "en") -> str:
    w = VERDICT_WORDS[lang]
    p = s.get("token_change")
    cost = "" if p is None else (w["same"] if abs(p) < 5 else (w["more"] if p > 0 else w["less"]).format(p=abs(p)))
    return w[s["verdict"]] + ((", " if lang == "en" else "，") + cost if cost else "")


def _arrow(s, k, fmt):
    a, b = s.get(f"{k}_none"), s.get(f"{k}_skill")
    return "-" if a is None or b is None else f"{fmt(a)} → {fmt(b)}"


def cmd_board(a) -> None:
    rows = [standing(n) for n in skill_names()]
    order = {"better": 0, "worse": 1, "format": 2, "none": 3}
    rows.sort(key=lambda s: ("verdict" not in s, order.get(s.get("verdict"), 9), s["skill"]))
    out = ["# Leaderboard", "",
           "Generated by `python bench.py board` from `results/`; the [report](https://opencolony-ai.github.io/skill-bench/) "
           "shows what Claude wrote, side by side. Each verifier runs the skill's cases twice on their own Claude Code, "
           "without and with the skill.", "",
           "- **Results**: cases where Claude did everything the task asked. Claude without the skill has a fair chance here.",
           "- **Follows the skill**: cases where Claude kept every rule the skill states (each rule quotes the skill). "
           "Without the skill Claude was never told these rules, so this shows the skill was read and obeyed, not that "
           "the work got better.",
           "- **Tokens** and **time** are for the whole set of cases, median over verifiers. Verifiers run on their own "
           "Claude subscription, so a run costs allowance, not money; tokens include Claude Code's own prompt read from cache.",
           f"- A result counts when at least {NEED} people other than the author agree within {TOLERANCE} case. "
           "**The model is reported by each verifier and not checked.**", "",
           "| Skill | Verdict | Results | Follows the skill | Tokens | Time | Claude used it | Verifiers |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in rows:
        n = s["cases"]
        link = f"[{s['skill']}](skills/{s['skill']}/SKILL.md)"
        if "verdict" not in s:
            out.append(f"| {link} | not yet run | - | - | - | - | - | 0/{NEED} |")
            continue
        out.append(f"| {link} | {verdict_text(s)} | {_arrow(s, 'result', lambda x: f'{x:g}/{n}')} | "
                   f"{_arrow(s, 'rule', lambda x: f'{x:g}/{n}')} | {_arrow(s, 'tokens', ktok)} | "
                   f"{_arrow(s, 'seconds', lambda x: f'{x:.0f} s')} | {s['used']}/{s['verifiers']} runs | "
                   f"{s['verifiers']}/{NEED} {STATUS_WORDS[s['status']]} |")
    out += ["", "Status: ✅ consistent (enough verifiers, and they agree) · ⚠️ disputed (they disagree; more are asked) · "
            "➖ no signal (Claude passes without the skill) · 🕓 self-reported (fewer than " + str(NEED) + " verifiers).",
            "Claude used it: in how many runs with the skill installed Claude opened it at all.", ""]
    text = "\n".join(out)
    if a.check:
        if (ROOT / "LEADERBOARD.md").read_text(encoding="utf-8") != text:
            raise BenchError("LEADERBOARD.md is out of date: run python bench.py board")
        return
    (ROOT / "LEADERBOARD.md").write_text(text, encoding="utf-8")
    print("wrote LEADERBOARD.md")


def cmd_site(a) -> None:
    import report
    for f in report.build(Path(a.out)):
        print(f"wrote {f}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("next"); p.add_argument("--user", default=""); p.set_defaults(fn=cmd_next)
    p = sub.add_parser("run"); p.add_argument("skill")
    p.add_argument("--model", default="sonnet", help="what Claude Code should use (default: sonnet)")
    p.add_argument("--claude", default="claude", help="path to the claude command")
    p.add_argument("--workdir", help="where the two runs happen (default: the system temp folder)")
    p.add_argument("--timeout", type=int, default=1200, help="seconds per run")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("submit"); p.add_argument("run"); p.add_argument("--user"); p.set_defaults(fn=cmd_submit)
    p = sub.add_parser("board"); p.add_argument("--check", action="store_true"); p.set_defaults(fn=cmd_board)
    p = sub.add_parser("site"); p.add_argument("--out", default="site"); p.set_defaults(fn=cmd_site)
    sub.add_parser("check-cases").set_defaults(fn=cmd_check_cases)
    p = sub.add_parser("verify"); p.add_argument("files", nargs="+"); p.add_argument("--author")
    p.set_defaults(fn=cmd_verify)
    a = ap.parse_args(argv)
    try:
        a.fn(a)
    except BenchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
