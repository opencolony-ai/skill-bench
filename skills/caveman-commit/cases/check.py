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
        "wrapped_72": all(len(l) <= 72 for l in lines),
        "dash_bullets": not any(l.lstrip().startswith("* ") for l in lines),
        "no_filler_words": not re.search(r"\b(I|We|we)\b", t) and not re.search(r"(?i)\b(this commit|now|currently|as requested)\b", t),
        "no_ai_attribution": not re.search(r"(?i)generated with|claude|\bAI\b", t),
        "breaking_marked": bool(m) and ((m.group(3) == "!") and "BREAKING CHANGE:" in t) == e["breaking"],
        "issue_reference": e.get("issue") is None or bool(re.fullmatch(rf"(Closes|Fixes|Refs) #{e['issue']}", last)),
        "describes_the_change": all(any(w.lower() in t.lower() for w in alts) for alts in e["mentions"]),
    }


def _rule(en, zh, quote, flag=None):
    return {"kind": "rule", "en": en, "zh": zh, "quote": quote, **({"flag": flag} if flag else {})}


ABOUT = {
    "describes_the_change": {"kind": "result", "en": "says what changed and what the task pointed out (the issue, the break)",
                             "zh": "寫出改了什麼，以及題目點出的事（issue、相容性破壞）"},
    "header_format": _rule("header is <type>(<scope>): <summary>", "標頭是 <type>(<scope>): <摘要>", "`<type>(<scope>): <imperative summary>`"),
    "type": _rule("the right Conventional Commits type", "Conventional Commits 類型選對", "Types: `feat`, `fix`, `refactor`"),
    "subject_max_72": _rule("first line at most 72 characters", "第一行最多 72 字元", "hard cap 72"),
    "no_trailing_period": _rule("no period at the end of the first line", "第一行結尾不加句號", "No trailing period"),
    "imperative": _rule("imperative mood: add, fix, remove", "祈使句：add、fix、remove", "Imperative mood"),
    "wrapped_72": _rule("body wrapped at 72 characters", "內文每行最多 72 字元", "Wrap at 72 chars"),
    "dash_bullets": _rule("bullets use - not *", "條列用 - 不用 *", "Bullets `-` not `*`", r"(?m)^\s*\* "),
    "no_filler_words": _rule("no I, we, now, currently, this commit", "不寫 I、we、now、currently、this commit",
                             '"I", "we", "now", "currently"', r"\b(I|We|we|[Nn]ow|[Cc]urrently|[Tt]his commit|[Aa]s requested)\b"),
    "no_ai_attribution": _rule("no AI attribution", "不寫 AI 署名", "any AI attribution", r"(?i)generated with|claude|\bAI\b"),
    "breaking_marked": _rule("a breaking change is marked with ! and BREAKING CHANGE:", "破壞性變更用 ! 和 BREAKING CHANGE: 標出", "BREAKING CHANGE:"),
    "issue_reference": _rule("ends with Closes/Fixes/Refs #n", "最後一行是 Closes/Fixes/Refs #n", "Reference issues/PRs at end"),
}
