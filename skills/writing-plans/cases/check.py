"""The plan structure writing-plans' SKILL.md requires, checked on plan.md: the header block, Global
Constraints with the spec's exact values, Review Focus, and tasks with Files, Interfaces and
checkbox steps that start from a failing test."""
import re


def _section(t, head):
    i = t.find(head)
    if i < 0:
        return ""
    j = t.find("\n## ", i + len(head))
    return t[i:j if j > 0 else None]


def check(folder, e):
    p = folder / "plan.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    tasks = re.split(r"(?m)^### Task \d+:", t)[1:]
    return {
        "exists": True,
        "title": bool(re.search(r"(?m)^# .+Implementation Plan\s*$", t)),
        "agentic_workers_note": "For agentic workers" in t and "- [ ]" in t,
        "header_fields": all(f"**{k}:**" in t for k in ("Goal", "Architecture", "Tech Stack", "Spec")),
        "global_constraints": all(any(v in _section(t, "## Global Constraints") for v in alts) for alts in e["constraints"]),
        "review_focus": "## Review Focus" in t,
        "tasks": len(tasks) >= 1,
        "files_per_task": bool(tasks) and all("**Files:**" in x and re.search(r"(Create|Modify|Test): `[^`]+`", x) for x in tasks),
        "interfaces_per_task": bool(tasks) and all("**Interfaces:**" in x for x in tasks),
        "checkbox_steps": bool(tasks) and all(re.search(r"(?m)^- \[ \] \*\*Step \d+", x) for x in tasks),
        # a step that runs the new test and expects it to fail, in whatever words
        "failing_test_first": bool(tasks) and all(re.search(r"(?i)fail", x) and re.search(r"(?i)\brun", x)
                                                  and re.search(r"(?i)expected", x) for x in tasks),
        "spec_values": all(any(v in t for v in alts) for alts in e["values"]),
    }


def _rule(en, zh, quote):
    return {"kind": "rule", "en": en, "zh": zh, "quote": quote}


ABOUT = {
    "spec_values": {"kind": "result", "en": "carries the spec's exact values (limits, names, files)", "zh": "帶到規格裡的確切數值（上限、名稱、檔案）"},
    "title": _rule("title: <feature> Implementation Plan", "標題：<功能> Implementation Plan", "# [Feature Name] Implementation Plan"),
    "agentic_workers_note": _rule("the note for agentic workers", "給代理執行者的說明", "**For agentic workers:**"),
    "header_fields": _rule("Goal, Architecture, Tech Stack, Spec", "Goal、Architecture、Tech Stack、Spec 四欄", "**Tech Stack:**"),
    "global_constraints": _rule("Global Constraints with the spec's values copied verbatim", "Global Constraints 逐字抄規格的數值", "exact values copied verbatim from the spec"),
    "review_focus": _rule("a Review Focus section", "有 Review Focus 一節", "## Review Focus"),
    "tasks": _rule("tasks headed ### Task N:", "任務以 ### Task N: 開頭", "### Task N: [Component Name]"),
    "files_per_task": _rule("each task lists its files", "每個任務列出檔案", "**Files:**"),
    "interfaces_per_task": _rule("each task states its interfaces", "每個任務寫出介面", "**Interfaces:**"),
    "checkbox_steps": _rule("steps as - [ ] checkboxes", "步驟用 - [ ] 勾選框", "Steps use checkbox (`- [ ]`) syntax for tracking"),
    "failing_test_first": _rule("each task starts from a failing test that is run", "每個任務從會失敗的測試開始並實際執行", "Write the failing test"),
}
