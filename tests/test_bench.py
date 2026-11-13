"""The tool's rules, without running Claude: results are made up from the cases' own reference
and trivial answers."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import bench

SKILL = "conventional-commit"


def answers(case, kind):
    d = case / "_bench" / kind
    return {p.name: p.read_text(encoding="utf-8") for p in d.iterdir()}


def fake_result(user, none_ok, skill_ok, skill=SKILL, version=None):
    """none_ok / skill_ok: how many cases pass in each arm (first n use the reference answer)."""
    arms = {}
    for arm, n in (("none", none_ok), ("skill", skill_ok)):
        cases = {}
        for i, c in enumerate(bench.case_dirs(skill)):
            out = answers(c, "ref" if i < n else "trivial")
            with tempfile.TemporaryDirectory() as tmp:
                bench.copy_inputs(c, Path(tmp))
                for fn, text in out.items():
                    (Path(tmp) / fn).write_text(text, encoding="utf-8")
                got = bench.checks.grade(bench.expect_of(c), tmp)
            cases[c.name] = {"pass": i < n, "checks": got, "outputs": out}
        arms[arm] = {"cases": cases, "usage": {"total_tokens": 1000}, "skill_used": arm == "skill"}
    return {"schema": bench.SCHEMA, "skill": skill, "version": version or bench.version(skill), "user": user,
            "finished": "2026-11-13T00:00:00+00:00", "arms": arms}


class Bench(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old = bench.RESULTS
        bench.RESULTS = self.tmp / "results"

    def tearDown(self):
        bench.RESULTS = self.old
        shutil.rmtree(self.tmp)

    def put(self, r):
        d = bench.RESULTS / r["skill"] / r["version"]
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{r['user'].lower()}--{len(list(d.iterdir()))}.json"
        f.write_text(json.dumps(r))
        return f

    def quiet(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = bench.main(list(argv))
        return code, buf.getvalue()

    # ------------------------------------------------------------ cases
    def test_every_case_tells_a_good_answer_from_a_bad_one(self):
        code, out = self.quiet("check-cases")
        self.assertEqual(code, 0, out)
        self.assertNotIn("BAD", out)

    def test_the_vague_control_uses_the_same_cases_but_has_its_own_version(self):
        self.assertEqual([c.name for c in bench.case_dirs("commit-tips")], [c.name for c in bench.case_dirs(SKILL)])
        self.assertNotEqual(bench.version("commit-tips"), bench.version(SKILL))

    # ------------------------------------------------------------ standing
    def test_status_follows_the_number_of_verifiers_and_their_agreement(self):
        self.assertEqual(bench.standing(SKILL)["status"], "not yet run")
        self.put(fake_result("ann", 0, 3))
        self.assertEqual(bench.standing(SKILL)["status"], "self-reported")
        self.put(fake_result("ben", 1, 3))
        self.put(fake_result("cai", 0, 2))
        s = bench.standing(SKILL)
        self.assertEqual((s["status"], s["none_median"], s["skill_median"], s["effect"]), ("consistent", 0, 3, 3))
        self.put(fake_result("dee", 3, 0))
        self.assertEqual(bench.standing(SKILL)["status"], "disputed")

    def test_cases_passed_without_the_skill_give_no_signal(self):
        for u in ("ann", "ben", "cai"):
            self.put(fake_result(u, 3, 3))
        self.assertEqual(bench.standing(SKILL)["status"], "no signal")

    def test_the_author_one_result_per_person_and_old_versions_do_not_count(self):
        self.put(fake_result("opencolony-ai", 0, 3))           # the author
        self.put(fake_result("ann", 0, 3))
        self.put(fake_result("ann", 0, 3))                     # the same person again
        self.put(fake_result("ben", 0, 3, version="000000000000"))  # an older version
        s = bench.standing(SKILL)
        self.assertEqual((s["verifiers"], s["users"], s["stale"]), (1, ["ann"], 1))

    def test_an_arm_that_could_not_run_is_not_counted_as_failing(self):
        r = fake_result("ann", 0, 3)
        r["arms"]["skill"]["could_not_run"] = "refused"
        self.put(r)
        self.assertEqual(bench.standing(SKILL)["verifiers"], 0)

    # ------------------------------------------------------------ next
    def test_next_is_chosen_for_you_and_never_your_own_or_one_you_did(self):
        _, a = self.quiet("next", "--user", "ann")
        _, b = self.quiet("next", "--user", "ann")
        self.assertEqual(a, b)                                  # same person, same day: same skill
        self.put(fake_result("ann", 0, 3))
        for _ in range(3):
            _, out = self.quiet("next", "--user", "ann")
            self.assertNotIn(SKILL + " ", out.splitlines()[0] + " ")
        for _ in range(3):                                      # an author is never sent to their own skills
            _, out = self.quiet("next", "--user", "opencolony-ai")
            pick = out.split()[0]
            self.assertNotEqual(bench.skill_meta(pick)["author"], "opencolony-ai")

    # ------------------------------------------------------------ what Claude did
    def test_the_stream_gives_the_result_and_whether_the_skill_was_opened(self):
        ev = [{"type": "system", "subtype": "init"},
              {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"},
                                                            {"type": "tool_use", "name": "Read", "input": {"file_path": "/w/case-1/task.md"}}]}},
              {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "pr"}}]}},
              {"type": "result", "num_turns": 3, "usage": {"input_tokens": 5}}]
        js, tools = bench._read_stream("\n".join(json.dumps(e) for e in ev) + "\nnot json\n")
        self.assertEqual(js["num_turns"], 3)
        self.assertEqual(bench._tool_counts(tools), {"Read": 1, "Skill": 1})
        self.assertTrue(bench._skill_used(tools, "pr"))
        self.assertFalse(bench._skill_used(tools, "grilling"))
        read = [{"type": "tool_use", "name": "Read", "input": {"file_path": "/w/.claude/skills/grilling/SKILL.md"}}]
        self.assertTrue(bench._skill_used(read, "grilling"))

    # ------------------------------------------------------------ skills with their own checker
    def test_a_skills_checker_is_part_of_its_version(self):
        name = "caveman-commit"
        f = bench.SKILLS / name / "cases" / "check.py"
        before, text = bench.version(name), f.read_text(encoding="utf-8")
        try:
            f.write_text(text + "\n# changed\n", encoding="utf-8")
            self.assertNotEqual(bench.version(name), before)
        finally:
            f.write_text(text, encoding="utf-8")
        self.assertEqual(bench.version(name), before)

    def test_a_supporting_file_of_the_skill_is_part_of_its_version(self):
        name = "internal-comms"
        f = bench.SKILLS / name / "examples" / "3p-updates.md"
        before, text = bench.version(name), f.read_text(encoding="utf-8")
        try:
            f.write_text(text + "\nchanged\n", encoding="utf-8")
            self.assertNotEqual(bench.version(name), before)
        finally:
            f.write_text(text, encoding="utf-8")

    def test_a_checker_that_breaks_on_odd_output_fails_the_case_instead_of_the_run(self):
        case = bench.case_dirs("writing-plans")[0]
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "plan.md").write_bytes(b"\xff\xfe not utf-8")
            r = bench.checks.grade(bench.expect_of(case), tmp)
        self.assertFalse(all(r.values()))

    def test_every_check_says_what_it_is_and_every_rule_quotes_its_skill(self):
        import re
        norm = lambda x: re.sub(r"\s+", " ", x).strip().lower()
        for name in bench.skill_names():
            meta = bench.skill_meta(name)
            if meta["cases_from"] != name or meta.get("exam"):   # exam items are checked once, by check-cases
                continue
            text = norm(" ".join(f.read_text(encoding="utf-8") for f in (bench.SKILLS / name).rglob("*.md")
                                 if "cases" not in f.relative_to(bench.SKILLS / name).parts))
            for c in bench.case_dirs(name):
                e = bench.expect_of(c)
                about = bench.checks.about(e)
                ref = next(p for p in (c / "_bench").iterdir() if p.name.startswith("ref"))
                with tempfile.TemporaryDirectory() as tmp:
                    bench.copy_inputs(c, Path(tmp))
                    for f in ref.iterdir():
                        shutil.copy2(f, Path(tmp) / f.name)
                    names = bench.checks.grade(e, tmp)
                for n in names:
                    self.assertIn(n, about, f"{name}/{c.name}: check {n} has no ABOUT entry")
                    a = about[n]
                    self.assertIn(a["kind"], ("result", "rule"), n)
                    self.assertTrue(a.get("en") and a.get("zh"), n)
                    if a["kind"] == "rule":  # a rule the skill does not state cannot be checked
                        self.assertIn(norm(a["quote"]), text, f"{name}: the quote for {n} is not in the skill")
                    if a.get("flag"):
                        re.compile(a["flag"])
                self.assertTrue(any(about[n]["kind"] == "result" and n != "exists" for n in names) or meta["author"] == "opencolony-ai",
                                f"{name}: an imported skill needs at least one result check")

    def test_the_verdict_reads_results_first_then_format_then_cost(self):
        base = {"result_none": 2, "result_skill": 2, "rule_none": 0, "rule_skill": 3, "tokens_none": 100_000, "tokens_skill": 150_000}
        self.assertEqual(bench.verdict(base), ("format", 50))
        self.assertEqual(bench.verdict({**base, "result_skill": 3})[0], "better")
        self.assertEqual(bench.verdict({**base, "result_skill": 1})[0], "worse")
        self.assertEqual(bench.verdict({**base, "rule_skill": 0})[0], "none")
        s = {**base, "verdict": "format", "token_change": 50}
        self.assertEqual(bench.verdict_text(s, "zh"), "結果一樣，只改了格式，多用 50% token")
        self.assertEqual(bench.verdict_text({**s, "token_change": -3}), "Same results, follows the skill's format, about the same tokens")

    def test_results_and_rules_are_counted_apart(self):
        r = fake_result("ann", 0, 3)
        ab = bench._abouts(SKILL)
        none, skill = bench.split(r, "none", ab), bench.split(r, "skill", ab)
        self.assertEqual((none["rule"], skill["rule"]), (0, 3))
        self.assertEqual(skill["result"], 3)

    def test_the_report_escapes_what_claude_wrote_and_runs_none_of_it(self):
        import report
        for u in ("ann", "bob", "cy"):
            r = fake_result(u, 0, 3)
            r["arms"]["skill"]["cases"]["case-1"]["outputs"] = {"COMMIT_MSG": "<script>alert(1)</script>",
                                                                 "page.html": "<script>alert(2)</script>"}
            self.put(r)
        out = self.tmp / "site"
        report.build(out)
        text = (out / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", text)
        self.assertIn('sandbox=""', text)
        self.assertIn("conventional-commit", text)
        self.assertIn("結果一樣", (out / "zh-TW.html").read_text(encoding="utf-8"))

    def test_finding_a_bug_counts_however_the_line_is_written(self):
        case = bench.case_dirs("caveman-review")[1]   # the bug is on line 2
        for text in ("**greet.js:2** - missing await", "Line 2: missing await", "第 2 行少了 await", "L2: missing await"):
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "review.md").write_text(text, encoding="utf-8")
                self.assertTrue(bench.checks.grade(bench.expect_of(case), tmp)["bugs_found"], text)

    def test_both_arms_start_from_a_warm_cache_and_the_warm_up_is_not_counted(self):
        import os, stat
        log = self.tmp / "calls.log"
        fake = self.tmp / "claude"
        fake.write_text("#!/bin/sh\n"
                        f"echo \"$2\" >> {log}\n"
                        "case \"$2\" in Reply*) cost=0.5;; *) cost=0.1;; esac\n"
                        "echo '{\"type\":\"result\",\"num_turns\":1,\"total_cost_usd\":'$cost',\"usage\":{\"input_tokens\":1}}'\n",
                        encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        out = bench.run_arm("caveman-commit", "skill", self.tmp / "arm", "sonnet", str(fake), 60)
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(calls[0].startswith("Reply with the single word OK"))
        self.assertTrue(calls[1].startswith("Do each task"))
        self.assertEqual(out["usage"]["cost_usd"], 0.1)
        self.assertEqual(out["warmup_usage"]["cost_usd"], 0.5)

    def test_a_refusal_records_where_it_pointed_not_what_it_wrote(self):
        d = {"tool_name": "Write", "tool_input": {"file_path": "/elsewhere/x.html", "content": "secret"}}
        self.assertEqual(bench._refused(d), "Write(/elsewhere/x.html)")
        self.assertEqual(bench._refused({"tool_name": "Bash", "tool_input": {"command": "ls"}}), "Bash")

    # ------------------------------------------------------------ the colony dashboard
    def test_every_skill_lives_in_exactly_one_colony(self):
        import report
        names = [s for c in report.colonies() for s in c["skills"]]
        self.assertEqual(sorted(names), sorted(bench.skill_names()))

    def test_points_reward_the_work_the_first_three_and_agreement(self):
        import report
        for u, (a, b) in {"ann": (0, 3), "bob": (0, 3), "cy": (1, 3), "dee": (0, 3), "eve": (3, 0)}.items():
            r = fake_result(u, a, b)
            r["finished"] = {"ann": "2026-11-13T01", "bob": "2026-11-13T02", "cy": "2026-11-13T03",
                             "dee": "2026-11-13T04", "eve": "2026-11-13T05"}[u]
            self.put(r)
        self.put(fake_result("opencolony-ai", 0, 3))          # the skill's author earns nothing on it
        pts = report.points()
        self.assertEqual(pts["ann"]["points"], 1 + 1 + 2)      # work, first three, agrees
        self.assertEqual(pts["cy"]["points"], 1 + 1 + 2)       # within one case of the median
        self.assertEqual(pts["dee"]["points"], 1 + 2)          # fourth: no pioneer point
        self.assertEqual(pts["eve"]["points"], 1)              # disagrees: still paid for the work, never less
        self.assertNotIn("opencolony-ai", pts)

    def test_points_wait_for_three_people_before_agreement_counts(self):
        import report
        self.put(fake_result("ann", 0, 3))
        self.assertEqual(report.points()["ann"]["points"], 2)
        self.assertEqual(report.points()["ann"]["pending"], 1)

    def test_the_colony_data_adds_up_and_the_page_draws_text_safely(self):
        import report
        self.put(fake_result("ann", 0, 3))
        d = json.loads(json.dumps(report.colony_data()))
        self.assertEqual(d["totals"]["skills"], len(bench.skill_names()))
        self.assertEqual(d["totals"]["with_results"], 1)
        self.assertEqual(d["totals"]["workers"], 1)
        item = next(s for c in d["colonies"] for s in c["skills"] if s["name"] == SKILL)
        self.assertEqual((item["verdict"], item["verifiers"]), ("format", 1))
        page = (bench.ROOT / "web" / "colony.html").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", page)
        self.assertNotIn("insertAdjacentHTML", page)

    def test_imported_skills_name_their_source_and_licence(self):
        for name in bench.skill_names():
            meta = bench.skill_meta(name)
            if meta["author"] != "opencolony-ai":
                self.assertTrue(meta.get("source", "").startswith("https://github.com/"), name)
                self.assertIn(meta.get("license"), ("MIT", "Apache-2.0"), name)
                self.assertTrue(any((bench.SKILLS / name / f).is_file() for f in ("LICENSE", "LICENSE.txt")), name)

    # ------------------------------------------------------------ verify
    def test_verify_accepts_an_honest_result_and_regrades_the_outputs(self):
        f = self.put(fake_result("ann", 1, 3))
        self.assertEqual(self.quiet("verify", str(f), "--author", "ann")[0], 0)

    def test_verify_refuses_a_claimed_pass_the_outputs_do_not_earn(self):
        r = fake_result("ann", 1, 3)
        r["arms"]["none"]["cases"]["case-3"]["pass"] = True    # its output is the trivial answer
        f = self.put(r)
        code, out = self.quiet("verify", str(f), "--author", "ann")
        self.assertEqual(code, 1)
        self.assertIn("re-graded False", out)

    def test_verify_refuses_another_persons_name_the_author_and_an_old_version(self):
        f = self.put(fake_result("ann", 0, 3))
        self.assertIn("pull request is by 'ben'", self.quiet("verify", str(f), "--author", "ben")[1])
        f = self.put(fake_result("opencolony-ai", 0, 3))
        self.assertIn("cannot verify their own skill", self.quiet("verify", str(f))[1])
        f = self.put(fake_result("cai", 0, 3, version="000000000000"))
        self.assertIn("not the current one", self.quiet("verify", str(f))[1])

    def test_verify_does_not_write_outside_its_scratch_folder(self):
        r = fake_result("ann", 0, 3)
        r["arms"]["none"]["cases"]["case-1"]["outputs"]["../../escape.txt"] = "x"
        f = self.put(r)
        self.quiet("verify", str(f))
        self.assertFalse((self.tmp / "escape.txt").exists())

    # ------------------------------------------------------------ board
    def test_board_lists_every_skill_with_its_status(self):
        for u in ("ann", "ben", "cai"):
            self.put(fake_result(u, 0, 3))
        old = bench.ROOT
        try:
            bench.ROOT = self.tmp
            self.quiet("board")
            text = (self.tmp / "LEADERBOARD.md").read_text()
        finally:
            bench.ROOT = old
        self.assertIn(f"| [{SKILL}](skills/{SKILL}/SKILL.md) | Same results, follows the skill's format, about the same tokens | 3/3 → 3/3 | 0/3 → 3/3 | 1k → 1k | - | 3/3 runs | 3/3 ✅ consistent |", text)
        for n in bench.skill_names():
            self.assertIn(f"[{n}]", text)


if __name__ == "__main__":
    unittest.main()
