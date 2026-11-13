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
            if meta["cases_from"] != name:
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
        base = {"result_none": 2, "result_skill": 2, "rule_none": 0, "rule_skill": 3, "cost_none": 0.10, "cost_skill": 0.15}
        self.assertEqual(bench.verdict(base), ("format", 50))
        self.assertEqual(bench.verdict({**base, "result_skill": 3})[0], "better")
        self.assertEqual(bench.verdict({**base, "result_skill": 1})[0], "worse")
        self.assertEqual(bench.verdict({**base, "rule_skill": 0})[0], "none")
        s = {**base, "verdict": "format", "cost_change": 50}
        self.assertEqual(bench.verdict_text(s, "zh"), "結果一樣，只改了格式，多花 50%")
        self.assertEqual(bench.verdict_text({**s, "cost_change": -3}), "Same results, follows the skill's format, about the same cost")

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
        self.assertIn(f"| [{SKILL}](skills/{SKILL}/SKILL.md) | Same results, follows the skill's format | 3/3 → 3/3 | 0/3 → 3/3 | - | - | 3/3 runs | 3/3 ✅ consistent |", text)
        for n in bench.skill_names():
            self.assertIn(f"[{n}]", text)


if __name__ == "__main__":
    unittest.main()
