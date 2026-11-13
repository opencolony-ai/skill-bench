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
        "separated": len(blocks) < 2 or len(re.findall(r"(?m)^---\s*$", t)) >= len(blocks) - 1,
        "about_the_plan": all(any(w.lower() in t.lower() for w in alts) for alts in e["topics"]),
    }
