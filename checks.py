"""Deterministic checks. Each case's `_bench/expect.json` names a check kind and its parameters;
`grade(expect, folder)` returns {check name: passed}. A case passes when every check passes.

Every check says what it is (`about(expect)`), in plain words, and of which kind:
  result  what the task itself asked for, so Claude without the skill has a fair chance at it.
          It must not depend on format: "line 3", "L3" and "第 3 行" all count.
  rule    what the skill tells Claude to do. It quotes the sentence of the skill it comes from
          (`quote`, found in the skill's files by the tests); a rule the skill does not state
          cannot be checked.

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


def _module(path: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location("case_check_" + Path(path).parent.parent.name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def script(folder: Path, e: dict) -> dict:
    """A skill's own checker: skills/<name>/cases/check.py defines check(folder, expect) -> {name: bool}
    and ABOUT (what each check is). It reads the files the agent wrote and never runs them. Like this
    file, it is reviewed in the pull request that adds the skill, and results are re-graded with the
    copy on main."""
    mod = _module(e["_script"])
    try:
        return {k: bool(v) for k, v in mod.check(Path(folder), e).items()}
    except Exception as x:  # odd output is a failed case, not a crashed run
        return {"checker_ran": False, f"error: {type(x).__name__}": False}


KINDS = {"script": script, "commit_message": commit_message, "changelog": changelog, "customer_csv": customer_csv,
         "cited_summary": cited_summary, "exact_answer": exact_answer}


def _r(en, zh):
    return {"kind": "result", "en": en, "zh": zh}


def _rule(en, zh, quote, flag=None):
    d = {"kind": "rule", "en": en, "zh": zh, "quote": quote}
    if flag:
        d["flag"] = flag  # a pattern the report highlights in the output when the check fails
    return d


COMMON = {"exists": _r("wrote the file the task asked for", "寫出題目要的檔案"),
          "checker_ran": _r("the output could be read", "產出讀得出來")}

ABOUT = {
    "commit_message": {
        "header_format": _rule("header is <type>(<scope>): <subject>", "標頭是 <type>(<scope>): <subject>", "`<type>(<scope>): <subject>`"),
        "type": _rule("the right type for the change", "類型選對", "Types: feat, fix, docs, refactor, test, chore."),
        "scope": _rule("scope is the top-level folder of the changed source", "範圍是改動程式所在的最上層資料夾", "The scope is the top-level directory"),
        "subject_rules": _rule("subject: imperative, lowercase start, no period, at most 50 characters", "主旨：祈使句、小寫開頭、不加句號、最多 50 字元", "imperative mood, starts with a lowercase letter, no trailing period, at most 50 characters"),
        "breaking_marker": _rule("a breaking change has ! before the colon", "破壞性變更在冒號前加 !", "adds `!`"),
        "blank_line_2": _rule("a blank line after the header", "標頭後空一行", "Then one blank line"),
        "wrapped_72": _rule("lines wrapped at 72 columns", "每行最多 72 字元", "wrapped at 72 columns"),
        "refs_footer": _rule("last line is Refs: <ticket> from the branch", "最後一行是分支裡的 Refs: <ticket>", "The last line is `Refs: <TICKET>`"),
        "breaking_footer": _rule("a breaking change has a BREAKING CHANGE: footer", "破壞性變更有 BREAKING CHANGE: 說明", "`BREAKING CHANGE: <what callers must change>`"),
    },
    "changelog": {
        "has_unreleased": _rule("entries go under ## [Unreleased]", "新條目放在 ## [Unreleased] 底下", "Add entries only under `## [Unreleased]`"),
        "released_unchanged": _rule("released versions are left alone", "已發布的版本不動", "Never edit a released version's section"),
        "section_set": _rule("each pull request in the section its labels say", "每個 PR 依標籤放到對的區段", "Labels to sections"),
        "section_order": _rule("sections in the fixed order", "區段依固定順序", "in this order and only when they have entries"),
        "entries_exact": _rule("entries written exactly in the format, ordered by number", "條目格式完全正確，依編號排序", "Entry: `- <title, without a trailing period>"),
        "skipped_labels": _rule("internal, ci and docs pull requests are left out", "internal、ci、docs 的 PR 不列", "are not listed"),
    },
    "customer_csv": {
        "header": _rule("the output columns, in order", "輸出欄位與順序", "Output columns: `id,name,email,phone,signup_date,updated_at`"),
        "row_ids": _rule("duplicates by email removed, latest kept, sorted by id", "依 email 去重、留最新、依 id 排序", "Duplicates are rows with the same email"),
        "emails": _rule("emails lowercased", "email 轉小寫", "Emails: lowercase."),
        "names": _rule("names trimmed, inner spaces collapsed", "姓名去頭尾空白、中間空白合併", "collapse runs of spaces inside names to one space"),
        "dates": _rule("dates written as YYYY-MM-DD, read day-first", "日期以日在前解讀，寫成 YYYY-MM-DD", "Write every date as `YYYY-MM-DD`."),
        "phones": _rule("phones in E.164 with +886", "電話轉成 +886 的 E.164", "Phones to E.164"),
        "log": _rule("cleanup_log.json with the four counts", "cleanup_log.json 有四個計數", "Also write `cleanup_log.json`"),
    },
    "cited_summary": {
        "all_numbers_cited": _rule("every number is followed by its source", "每個數字後面都附出處", "Every number you write is followed immediately by its source"),
        "citations_point_right": _rule("each source line really holds that number", "出處那一行真的有這個數字", "the line of that input file where the number appears"),
        "calc_inputs_cited": _rule("computed numbers use only cited numbers", "算出來的數字只用有出處的數字", "using only numbers you cite"),
        "answers": _r("answers the questions with the right numbers", "答對題目問的數字"),
    },
    "exact_answer": {"answer": _r("the right answer", "答案正確")},
}


def about(expect: dict) -> dict:
    """{check name: {kind, en, zh, quote?, flag?}} for the checks of this case's kind."""
    kind = expect.get("check")
    own = getattr(_module(expect["_script"]), "ABOUT", {}) if kind == "script" else ABOUT.get(kind, {})
    return {**COMMON, **own}


def grade(expect: dict, folder) -> dict:
    kind = expect.get("check")
    if kind not in KINDS:
        raise ValueError(f"unknown check kind {kind!r} (known: {', '.join(sorted(KINDS))})")
    return KINDS[kind](Path(folder), expect)
