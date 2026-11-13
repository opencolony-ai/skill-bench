"""Rules from caveman-review's SKILL.md, checked on review.md: one line per finding with its line
number, no hedging, and the planted bugs found."""
import re

FIND = re.compile(r"^(?:`?[\w./-]+`?:)?L(\d+)(?:-L?(\d+))?: \S")
HEDGE = re.compile(r"(?i)\b(perhaps|maybe|i think|i noticed|it seems|it looks like|might want|you may want|consider|just a suggestion|probably)\b")


def check(folder, e):
    p = folder / "review.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"(?m)^```[\w-]*\s*$", "", t)
    lines = [re.sub(r"^[-*]\s+", "", l.strip()) for l in t.splitlines() if l.strip()]
    found = [(l, FIND.match(l)) for l in lines]
    hits = [(int(m.group(1)), int(m.group(2) or m.group(1))) for _, m in found if m]
    others = [l for l, m in found if not m]
    return {
        "exists": True,
        "one_line_per_finding": bool(hits) and len(others) <= 1,   # one line of overall remarks at the top is allowed
        "no_hedging": not HEDGE.search(t),
        "short_lines": all(len(l) <= 200 for l, m in found if m),
        "bugs_found": all(any(a <= b <= z for a, z in hits for b in alts) for alts in e["bugs"]),
    }
