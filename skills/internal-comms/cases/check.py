"""The 3P format from internal-comms' examples/3p-updates.md, checked on update.md: an emoji, the team
and the dates on the first line, then exactly Progress / Plans / Problems, 1-3 sentences each, no
other formatting."""
import re


def _sentences(s):
    return len([x for x in re.split(r"(?<=[.!?])\s+", s.strip()) if x.strip()])


def check(folder, e):
    p = folder / "update.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"(?m)^```[\w-]*\s*$", "", t)
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    head = lines[0] if lines else ""
    secs = [l.split(":", 1) for l in lines[1:4]]
    names = [s[0].strip() for s in secs]
    return {
        "exists": True,
        "four_lines": len(lines) == 4,
        "header_line": bool(head) and ord(head[0]) > 0x2000 and e["team"].lower() in head.lower()
                       and any(d.lower() in head.lower() for d in e["dates"]),
        "sections_in_order": names == ["Progress", "Plans", "Problems"],
        "one_to_three_sentences": len(secs) == 3 and all(len(s) == 2 and 1 <= _sentences(s[1]) <= 3 for s in secs),
        "no_other_formatting": not re.search(r"(?m)^\s*(#|[-*+] |\d+[.)] )", t) and "**" not in t and "__" not in t,
        "has_the_numbers": all(any(v in t for v in alts) for alts in e["facts"]),
    }
