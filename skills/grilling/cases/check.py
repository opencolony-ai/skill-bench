"""The round format from grilling's SKILL.md, checked on questions.md: numbered questions written as
`❓ **Qn** - **title**: ...`, each with a recommended answer `➡️ ...`, separated by `---`."""
import re

Q = re.compile(r"❓\s*\*\*Q(\d+)\*\*\s*[-–—]\s*\*\*[^*\n]+\*\*\s*:")


def check(folder, e):
    p = folder / "questions.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    nums = [int(m.group(1)) for m in Q.finditer(t)]
    blocks = t.split("❓")[1:]
    return {
        "exists": True,
        "question_format": len(nums) >= 3 and len(nums) == len(blocks),
        "numbered_from_1": nums == list(range(1, len(nums) + 1)),
        "recommended_answers": bool(blocks) and all("➡" in b for b in blocks),
        "asks_questions": t.count("?") >= 3,
        "about_the_plan": all(any(w.lower() in t.lower() for w in alts) for alts in e["topics"]),
    }


ABOUT = {
    "asks_questions": {"kind": "result", "en": "asks at least three questions", "zh": "至少問了三個問題"},
    "about_the_plan": {"kind": "result", "en": "the questions are about this plan's weak points", "zh": "問題針對這份計畫的弱點"},
    "question_format": {"kind": "rule", "en": "questions written as ❓ **Qn** - **title**:", "zh": "問題寫成 ❓ **Qn** - **標題**:",
                        "quote": "❓ **Q1** - **<question title>**"},
    "numbered_from_1": {"kind": "rule", "en": "questions numbered 1, 2, 3 ...", "zh": "問題依序編號", "quote": "number each question"},
    "recommended_answers": {"kind": "rule", "en": "each question comes with a recommended answer ➡️", "zh": "每題附上建議答案 ➡️",
                            "quote": "give your recommended answer"},
}
