#!/usr/bin/env python3
"""The judge: layers 2-4 of a shared exam, answered by Claude from screenshots and code.

    python graders/judge.py questions <item-dir> <output-dir> [--model opus]
        layer 2 yes/no questions from item.json "judge", and layer 3: the judge sees only the first screen
        and answers item.json "questions"; a program compares the answers with the brief's ("answer_any").
    python graders/judge.py pair <item-dir> <output-a> <output-b> [--model opus]
        layer 4: which of two pages better serves the brief, judged twice with the sides swapped; it counts
        only when both orders agree, otherwise it is a tie.

Meant to run on the maintainer's schedule (Claude Code on a subscription), with one pinned model; every
judgement records the model that actually served it. The judge only reads files: no shell, no web.
Prints one JSON object.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GRADER = Path(__file__).resolve().parent / "web" / "grade_item.cjs"


def shots(item: Path, out: Path, work: Path) -> dict:
    """Render the output with the exam grader; returns its measurements and leaves screenshots in work."""
    p = subprocess.run(["node", str(GRADER), str(item), str(out), str(work)], capture_output=True, text=True, timeout=900)
    return json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 and p.stdout.strip() else {}


def ask(prompt: str, where: Path, model: str, claude: str = "claude") -> tuple[dict, list[str]]:
    """One judge session in `where`; returns (the JSON object it answered, models that served it)."""
    p = subprocess.run([claude, "-p", prompt, "--output-format", "json", "--model", model, "--max-turns", "12",
                        "--permission-mode", "default", "--setting-sources", "project,local", "--strict-mcp-config",
                        "--allowedTools", "Read", "--disallowedTools", "Bash", "Write", "Edit", "WebFetch", "WebSearch"],
                       cwd=where, capture_output=True, text=True, timeout=900)
    try:
        js = json.loads(p.stdout)
    except ValueError:
        return {}, []
    models = sorted((js.get("modelUsage") or {}).keys())
    m = re.search(r"\{.*\}", js.get("result") or "", re.S)
    try:
        return (json.loads(m.group(0)) if m else {}), models
    except ValueError:
        return {}, models


def questions(item: Path, out: Path, model: str) -> dict:
    spec = json.loads((item / "_bench" / "item.json").read_text(encoding="utf-8"))
    brief = (item / "task.md").read_text(encoding="utf-8")
    res = {"item": item.name, "judge": {}, "understood": {}}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shots(item, out, work / "shots")
        # layer 3: first screen only, nothing else, no brief
        seen = work / "seen"
        seen.mkdir()
        for w in ("1280", "320"):
            src = work / "shots" / f"first-{w}.png"
            if src.exists():
                shutil.copy2(src, seen / f"first-screen-{w}.png")
        qs = spec.get("questions") or []
        if qs:
            prompt = ("You are a first-time visitor. Look only at first-screen-1280.png and first-screen-320.png in this folder "
                      "(the first screen of one web page, on a laptop and on a phone; read them with the Read tool). Do not "
                      "guess beyond what they show. Answer each question in a few words; if the first screen does not tell "
                      "you, answer \"not shown\". Reply with only a JSON object mapping each id to your answer.\n\n" +
                      "\n".join(f"{q['id']}: {q['question']}" for q in qs))
            ans, models = ask(prompt, seen, model)
            for q in qs:
                a = str(ans.get(q["id"], ""))
                res["understood"][q["id"]] = {"answer": a, "right": any(x.lower() in a.lower() for x in q["answer_any"])}
            res["understood_models"] = models
        # layer 2 judge questions: the brief, the code and the screenshots
        js = spec.get("judge") or []
        if js:
            look = work / "look"
            look.mkdir()
            for f in out.iterdir():
                if f.is_file() and f.suffix in (".html", ".css", ".js", ".md"):
                    shutil.copy2(f, look / f.name)
            for f in (work / "shots").glob("*.png"):
                shutil.copy2(f, look / f.name)
            (look / "BRIEF.md").write_text(brief, encoding="utf-8")
            prompt = ("BRIEF.md is a brief; the other files are what someone built for it (code, and screenshots named "
                      "full-<width>.png and first-<width>.png). Read them. Answer each question strictly yes or no, judging "
                      "only what the files show. Reply with only a JSON object mapping each id to \"yes\" or \"no\".\n\n" +
                      "\n".join(f"{q['id']}: {q['question']}" for q in js))
            ans, models = ask(prompt, look, model)
            res["judge"] = {q["id"]: str(ans.get(q["id"], "")).strip().lower().startswith("y") for q in js}
            res["judge_models"] = models
    return res


def pair(item: Path, a: Path, b: Path, model: str, seed: int = 0) -> dict:
    brief = (item / "task.md").read_text(encoding="utf-8")
    verdicts, models = [], []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name, out in (("a", a), ("b", b)):
            shots(item, out, work / name)
        for order in ((("a", "b")), (("b", "a"))):          # both orders: a position bias cancels out
            look = work / f"look-{order[0]}{order[1]}"
            look.mkdir()
            (look / "BRIEF.md").write_text(brief, encoding="utf-8")
            for label, src in zip(("left", "right"), order):
                for w in ("1280", "320"):
                    f = work / src / f"full-{w}.png"
                    if f.exists():
                        shutil.copy2(f, look / f"{label}-{w}.png")
                page = (a if src == "a" else b) / "index.html"
                if page.exists():
                    shutil.copy2(page, look / f"{label}.html")
            prompt = ("BRIEF.md is a brief. Two people each built a page for it: left-*.png and left.html, right-*.png and "
                      "right.html (screenshots at 1280 and 320 pixels wide, and the code). Read them all. Which page better "
                      "serves the brief and the people it is for: clearer, more usable, more fitting, better made? Judge the "
                      "pages, not their length. Reply with only a JSON object: {\"better\": \"left\" | \"right\" | \"tie\", "
                      "\"why\": \"one sentence\"}.")
            ans, m = ask(prompt, look, model)
            models += m
            v = str(ans.get("better", "")).lower()
            winner = order[0] if v == "left" else order[1] if v == "right" else "tie"
            verdicts.append({"order": "".join(order), "said": v, "winner": winner, "why": ans.get("why", "")})
    both = {v["winner"] for v in verdicts}
    return {"item": item.name, "a": str(a), "b": str(b), "verdicts": verdicts,
            "winner": next(iter(both)) if len(both) == 1 else "tie", "models": sorted(set(models))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("questions"); q.add_argument("item"); q.add_argument("out"); q.add_argument("--model", default="opus")
    p = sub.add_parser("pair"); p.add_argument("item"); p.add_argument("a"); p.add_argument("b"); p.add_argument("--model", default="opus")
    a = ap.parse_args()
    if a.cmd == "questions":
        r = questions(Path(a.item), Path(a.out), a.model)
    else:
        r = pair(Path(a.item), Path(a.a), Path(a.b), a.model)
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
