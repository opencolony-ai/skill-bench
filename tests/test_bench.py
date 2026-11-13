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
            cases[c.name] = {"pass": i < n, "checks": {}, "outputs": out}
        arms[arm] = {"cases": cases, "usage": {"total_tokens": 1000}}
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
        _, out = self.quiet("next", "--user", "opencolony-ai")
        self.assertIn("Nothing needs a verifier", out)          # the author of every seed skill

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
        self.assertIn(f"| [{SKILL}](skills/{SKILL}/SKILL.md) | ✅ consistent | 0/3 | 3/3 | +3 | 3/3 |", text)
        for n in bench.skill_names():
            self.assertIn(f"[{n}]", text)


if __name__ == "__main__":
    unittest.main()
