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
        "emoji_team_dates_first": bool(head) and ord(head[0]) > 0x2000 and e["team"].lower() in head.lower()
                                  and any(d.lower() in head.lower() for d in e["dates"]),
        "team_and_week": e["team"].lower() in t.lower() and any(d.lower() in t.lower() for d in e["dates"]),
        "sections_in_order": names == ["Progress", "Plans", "Problems"],
        "one_to_three_sentences": len(secs) == 3 and all(len(s) == 2 and 1 <= _sentences(s[1]) <= 3 for s in secs),
        "no_other_formatting": not re.search(r"(?m)^\s*(#|[-*+] |\d+[.)] )", t) and "**" not in t and "__" not in t,
        "has_the_numbers": all(any(v in t for v in alts) for alts in e["facts"]),
    }


FORMATTING = r"(?m)^\s*(#+ |[-*+] |\d+[.)] )|\*\*|__"
ABOUT = {
    "team_and_week": {"kind": "result", "en": "names the team and the week asked for", "zh": "寫出題目給的團隊和那一週"},
    "has_the_numbers": {"kind": "result", "en": "carries the key facts from the notes", "zh": "帶到筆記裡的關鍵數字與事項"},
    "four_lines": {"kind": "rule", "en": "exactly four lines: title, Progress, Plans, Problems", "zh": "剛好四行：標題、Progress、Plans、Problems",
                   "quote": "The format is always the same, very strict formatting"},
    "emoji_team_dates_first": {"kind": "rule", "en": "first line: an emoji, the team, the dates", "zh": "第一行：表情符號、團隊、日期",
                               "quote": "[pick an emoji] [Team Name] (Dates Covered"},
    "sections_in_order": {"kind": "rule", "en": "Progress:, Plans:, Problems: in that order", "zh": "依序是 Progress:、Plans:、Problems:",
                          "quote": "Progress: [1-3 sentences of content]"},
    "one_to_three_sentences": {"kind": "rule", "en": "each section 1-3 sentences", "zh": "每段 1–3 句",
                               "quote": "Each section should be no more than 1-3 sentences"},
    "no_other_formatting": {"kind": "rule", "en": "no headings, bullets or bold", "zh": "沒有標題、條列或粗體",
                            "quote": "Never use any formatting other than this", "flag": FORMATTING},
}
