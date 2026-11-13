"""Rules from caveman-commit's SKILL.md, checked on COMMIT_MSG."""
import re

TYPES = "feat|fix|refactor|perf|docs|test|chore|build|ci|style|revert"
THIRD = {"adds", "fixes", "removes", "updates", "changes", "makes", "uses", "renames", "caches", "moves",
         "handles", "returns", "prevents", "improves", "supports", "allows", "bumps", "compiles", "drops"}
ED_OK = {"embed", "shed", "seed", "need", "speed", "feed", "bed", "red", "bleed", "breed", "proceed", "exceed"}


def check(folder, e):
    p = folder / "COMMIT_MSG"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8").strip()
    t = re.sub(r"^```[\w-]*\n", "", t)            # a fenced block is fine: the skill outputs one
    t = re.sub(r"\n```$", "", t).strip("\n")
    lines = t.split("\n")
    m = re.match(rf"^({TYPES})(\([a-z0-9._/-]+\))?(!)?: (\S.*)$", lines[0])
    subj = m.group(4) if m else ""
    first = subj.split(" ")[0].lower() if subj else ""
    last = [l.strip() for l in lines if l.strip()][-1]
    return {
        "exists": True,
        "header_format": bool(m),
        "type": bool(m) and m.group(1) in e["types"],
        "subject_max_72": len(lines[0]) <= 72,
        "no_trailing_period": not lines[0].rstrip().endswith("."),
        "imperative": bool(first) and first not in THIRD and (first in ED_OK or not re.search(r"(ed|ing)$", first)),
        "blank_line_after_subject": len(lines) == 1 or lines[1] == "",
        "wrapped_72": all(len(l) <= 72 for l in lines),
        "dash_bullets": not any(l.lstrip().startswith("* ") for l in lines),
        "no_filler_words": not re.search(r"\b(I|We|we)\b", t) and not re.search(r"(?i)\b(this commit|now|currently|as requested)\b", t),
        "no_ai_attribution": not re.search(r"(?i)generated with|claude|\bAI\b", t),
        "breaking_marked": bool(m) and ((m.group(3) == "!") and "BREAKING CHANGE:" in t) == e["breaking"],
        "issue_reference": e.get("issue") is None or bool(re.fullmatch(rf"(Closes|Fixes|Refs) #{e['issue']}", last)),
    }
