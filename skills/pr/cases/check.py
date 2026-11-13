"""The PR body template from pr's SKILL.md, checked on PR_BODY.md: exactly Summary / Evidence /
Merge Danger with no preamble, a visual in Summary, Before/After evidence, the door named correctly
and a short blast radius."""
import re


def _section(t, head):
    m = re.search(rf"(?m)^## {re.escape(head)}\s*$", t)
    if not m:
        return ""
    n = re.search(r"(?m)^## ", t[m.end():])
    return t[m.end(): m.end() + n.start() if n else None]


def check(folder, e):
    p = folder / "PR_BODY.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    heads = [h.strip() for h in re.findall(r"(?m)^## (.+)$", t)]
    first = next((l.strip() for l in t.splitlines() if l.strip()), "")
    ev, md = _section(t, "Evidence"), _section(t, "Merge Danger")
    door = re.search(r"(?i)\*\*Door:\*\*\s*(one-way|two-way)", md)
    blast = re.search(r"\*\*Blast Radius:\*\*\s*([^\n]+)", md)
    return {
        "exists": True,
        "sections": heads == ["Summary", "Evidence", "Merge Danger"],
        "no_preamble": first == "## Summary",
        "summary_visual": "```" in _section(t, "Summary"),
        "before_after": "**Before:**" in ev and "**After:**" in ev,
        "door": bool(door) and door.group(1).lower() == e["door"],
        "blast_radius": bool(blast) and 1 <= len(re.findall(r"[A-Za-z][\w-]*", blast.group(1))) <= 3,
        "carries_the_evidence": all(any(w.lower() in t.lower() for w in alts) for alts in e["mentions"]),
    }


def _rule(en, zh, quote):
    return {"kind": "rule", "en": en, "zh": zh, "quote": quote}


ABOUT = {
    "carries_the_evidence": {"kind": "result", "en": "carries the test evidence and the key risk given in the change",
                             "zh": "帶到變更裡給的測試證據和主要風險"},
    "sections": _rule("exactly Summary, Evidence, Merge Danger", "剛好是 Summary、Evidence、Merge Danger 三節", "Use this template for writing the PR body"),
    "no_preamble": _rule("starts straight with ## Summary", "直接從 ## Summary 開始", "Skip all preambles"),
    "summary_visual": _rule("Summary shows a diagram, diff-sketch or tree", "Summary 用圖、diff 草圖或樹狀圖呈現", "<diagram, diff-sketch, or tree>"),
    "before_after": _rule("evidence as Before / After", "證據寫成 Before / After", "**Before:**"),
    "door": _rule("names the door correctly: one-way or two-way", "正確判斷單向門或雙向門", "Describe whether it's a one-way or two-way door"),
    "blast_radius": _rule("a short blast radius", "簡短的影響範圍", "**Blast Radius:** <one-word description>"),
}
