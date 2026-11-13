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
