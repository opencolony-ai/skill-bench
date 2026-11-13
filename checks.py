"""Deterministic checks. Each case's `_bench/expect.json` names a check kind and its parameters;
`grade(expect, folder)` returns {check name: passed}. A case passes when every check passes.

Adding a kind is a pull request to this file, reviewed like code: results are always re-graded
with the checks on the main branch, never with a contributor's copy."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def _read(folder: Path, name: str):
    f = folder / name
    try:
        return f.read_text(encoding="utf-8") if f.is_file() else None
    except (OSError, UnicodeDecodeError):
        return None


def commit_message(folder: Path, e: dict) -> dict:
    t = _read(folder, e.get("file", "COMMIT_MSG"))
    if t is None:
        return {"exists": False}
    lines = t.strip("\n").split("\n")
    m = re.match(r"^(feat|fix|docs|refactor|test|chore)\(([a-z0-9-]+)\)(!)?: (.+)$", lines[0])
    subj = m.group(4) if m else ""
    body = [l for l in lines if l.strip()]
    return {
        "exists": True,
        "header_format": bool(m),
        "type": bool(m) and m.group(1) in e["types"],
        "scope": bool(m) and m.group(2) == e["scope"],
        "subject_rules": bool(m) and len(subj) <= 50 and subj[:1].islower() and not subj.endswith("."),
        "breaking_marker": bool(m) and (m.group(3) == "!") == e["breaking"],
        "blank_line_2": len(lines) > 2 and lines[1] == "",
        "wrapped_72": all(len(l) <= 72 for l in lines),
        "refs_footer": bool(body) and body[-1].strip() == f"Refs: {e['ticket']}",
        "breaking_footer": any(l.startswith("BREAKING CHANGE: ") for l in lines) == e["breaking"],
    }


def changelog(folder: Path, e: dict) -> dict:
    t = _read(folder, "CHANGELOG.md")
    if t is None:
        return {"exists": False}
    i = t.find("## [Unreleased]")
    rel = t.find(e["released_heading"])
    out = {"exists": True, "has_unreleased": i >= 0 and (rel < 0 or i < rel),
           "released_unchanged": rel >= 0 and t[rel:].strip() == e["released"].strip()}
    secs, cur = {}, None
    if i >= 0:
        for line in t[i:rel if rel > i else None].splitlines()[1:]:
            if line.startswith("### "):
                cur = line[4:].strip()
                secs.setdefault(cur, [])
            elif line.startswith("- ") and cur:
                secs[cur].append(line.rstrip())
    want = e["sections"]
    order = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
    out["section_set"] = set(secs) == set(want)
    out["section_order"] = list(secs) == [s for s in order if s in secs]
    out["entries_exact"] = all(secs.get(s) == v for s, v in want.items())
    out["skipped_labels"] = not any(w in t for w in e.get("must_not_appear", []))
    return out


def customer_csv(folder: Path, e: dict) -> dict:
    t = _read(folder, "clean.csv")
    if t is None:
        return {"exists": False}
    rows = list(csv.DictReader(t.splitlines()))
    hdr = t.splitlines()[0].strip().split(",") if t.strip() else []
    want = e["rows"]
    by = {r.get("id"): r for r in rows}
    try:
        log = json.loads(_read(folder, "cleanup_log.json") or "null")
    except ValueError:
        log = None
    return {
        "exists": True,
        "header": hdr == e["columns"],
        "row_ids": [r.get("id") for r in rows] == [r["id"] for r in want],
        "emails": all(by.get(r["id"], {}).get("email") == r["email"] for r in want),
        "names": all(by.get(r["id"], {}).get("name") == r["name"] for r in want),
        "dates": all(by.get(r["id"], {}).get(k) == r[k] for r in want for k in ("signup_date", "updated_at")),
        "phones": all(by.get(r["id"], {}).get("phone") == r["phone"] for r in want),
        "log": log == e["log"],
    }


_NUM = re.compile(r"(?<![\w.,#:\[])-?\d[\d,]*(?:\.\d+)?%?")


def cited_summary(folder: Path, e: dict) -> dict:
    """Every number carries [file:Lnn] (that line holds the number) or [calc: ...] whose inputs are
    themselves numbers cited in the summary; list markers, quarter names and years are not numbers."""
    t = _read(folder, "summary.md")
    if t is None:
        return {"exists": False}
    tags = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"\[([^\]]+)\]", t)]
    masked = re.sub(r"\[[^\]]+\]", lambda m: " " * len(m.group(0)), t)
    lines = {fn: (_read(folder, fn) or "").splitlines() for fn in e["files"]}
    cited, nums, bad, missing = set(), [], [], []
    for m in _NUM.finditer(masked):
        s = m.group(0).rstrip(",")
        if re.search(r"(Q|FY)$", masked[max(0, m.start() - 2):m.start()]) or re.fullmatch(r"(19|20)\d\d", s):
            continue
        line_start = masked.rfind("\n", 0, m.start()) + 1
        if masked[line_start:m.start()].strip() == "" and re.match(r"[.)]\s", masked[m.end():m.end() + 2]):
            continue
        nxt = next((g for g in tags if g[0] >= m.end() and t[m.end():g[0]].strip() == ""), None)
        nums.append(s)
        if not nxt:
            missing.append(s)
            continue
        tag = nxt[2].strip()
        mm = re.fullmatch(r"([\w.-]+):L(\d+)", tag)
        if mm:
            fn, ln = mm.group(1), int(mm.group(2))
            if fn in lines and 1 <= ln <= len(lines[fn]) and s.rstrip("%") in lines[fn][ln - 1]:
                cited.add(s.replace(",", ""))
            else:
                bad.append(f"{s}->{tag}")
        elif tag.startswith("calc:"):
            cited.add(s.rstrip("%").replace(",", ""))
        else:
            bad.append(f"{s}->{tag}")
    calc_ok = all(v.replace(",", "") in cited for _, _, g in tags if g.strip().startswith("calc:")
                  for v in re.findall(r"\d[\d,]*(?:\.\d+)?", g.split(":", 1)[1]))
    return {"exists": True, "all_numbers_cited": not missing and bool(nums), "citations_point_right": not bad,
            "calc_inputs_cited": calc_ok, "answers": all(f in masked for f in e["facts"])}


def exact_answer(folder: Path, e: dict) -> dict:
    t = _read(folder, e.get("file", "answer.txt"))
    return {"answer": t is not None and t.strip().replace(" ", "").lower() == str(e["answer"]).lower()}


def script(folder: Path, e: dict) -> dict:
    """A skill's own checker: skills/<name>/cases/check.py defines check(folder, expect) -> {name: bool}.
    It reads the files the agent wrote and never runs them. Like this file, it is reviewed in the pull
    request that adds the skill, and results are re-graded with the copy on main."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("case_check_" + Path(e["_script"]).parent.parent.name, e["_script"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        return {k: bool(v) for k, v in mod.check(Path(folder), e).items()}
    except Exception as x:  # odd output is a failed case, not a crashed run
        return {"checker_ran": False, f"error: {type(x).__name__}": False}


KINDS = {"script": script, "commit_message": commit_message, "changelog": changelog, "customer_csv": customer_csv,
         "cited_summary": cited_summary, "exact_answer": exact_answer}


def grade(expect: dict, folder) -> dict:
    kind = expect.get("check")
    if kind not in KINDS:
        raise ValueError(f"unknown check kind {kind!r} (known: {', '.join(sorted(KINDS))})")
    return KINDS[kind](Path(folder), expect)
