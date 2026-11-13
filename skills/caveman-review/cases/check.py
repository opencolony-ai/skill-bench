"""Rules from caveman-review's SKILL.md, checked on review.md: one line per finding with its line
number, no hedging, and the planted bugs found."""
import re

FIND = re.compile(r"^(?:`?[\w./-]+`?:)?L(\d+)(?:-L?(\d+))?: \S")
HEDGE = r"(?i)\b(perhaps|maybe|i think|i noticed|it seems|might want|consider|just a suggestion)\b"


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
    # where the review points, in any wording ("L3", "line 3", "lines 8-9"): finding the bug is
    # checked apart from the format
    named = [(int(a), int(b or a)) for a, b in re.findall(
        r"(?i)(?:\bL|\blines?\s+|\.\w{1,4}:|#L|第\s*)(\d+)(?:\s*[-–]\s*L?(\d+))?", t)]
    return {
        "exists": True,
        "one_line_per_finding": bool(hits) and len(others) <= 1,   # one line of overall remarks at the top is allowed
        "no_hedging": not re.search(HEDGE, t),
        "bugs_found": all(any(a <= b <= z for a, z in named for b in alts) for alts in e["bugs"]),
    }


ABOUT = {
    "bugs_found": {"kind": "result", "en": "points at the line of every planted bug, in any wording",
                   "zh": "指出每個埋好的 bug 所在的行（怎麼寫都算）"},
    "one_line_per_finding": {"kind": "rule", "en": "one line per finding, starting with L<line>:",
                             "zh": "一個問題一行，以 L<行號>: 開頭", "quote": "One line per finding"},
    "no_hedging": {"kind": "rule", "en": "no hedging: perhaps, maybe, I think, consider",
                   "zh": "不含糊其詞：perhaps、maybe、I think、consider",
                   "quote": 'Hedging ("perhaps", "maybe", "I think")', "flag": HEDGE},
}
