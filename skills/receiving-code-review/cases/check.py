"""receiving-code-review's SKILL.md on reply.md: no performative agreement or thanks, push back on
the suggestion the code contradicts (citing what shows it), call out the unused feature (YAGNI), and
ask about the unclear item instead of guessing."""
import re

PERFORM = re.compile(r"(?i)you'?re (absolutely |totally |completely )?right|great (point|catch|suggestion|feedback|question)|excellent (point|feedback|catch)|let me implement")
THANKS = re.compile(r"(?i)\bthank|\bappreciate|\bgrateful")
UNUSED = ["unused", "not used", "isn't used", "is not used", "never used", "not called", "isn't called", "never called",
          "no callers", "no caller", "nothing calls", "no one calls", "nobody calls", "yagni", "not referenced",
          "unreferenced", "no references", "not registered", "isn't registered", "never registered", "not wired",
          "no route", "not mounted", "dead code"]


def check(folder, e):
    p = folder / "reply.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    low = t.lower()
    return {
        "exists": True,
        "no_performative_agreement": not PERFORM.search(t),
        "no_thanks": not THANKS.search(t),
        "pushback_with_evidence": all(w.lower() in low for w in e["evidence"]),
        "yagni_called_out": any(w in low for w in UNUSED) and e["unused"].lower() in low,
        "asks_about_unclear_item": "?" in t,
    }


ABOUT = {
    "pushback_with_evidence": {"kind": "result", "en": "refuses the suggestion the code contradicts, citing what shows it",
                               "zh": "拒絕程式碼證明是錯的建議，並指出證據"},
    "yagni_called_out": {"kind": "result", "en": "notices the feature to extend is not used anywhere", "zh": "發現要擴充的功能根本沒人用"},
    "asks_about_unclear_item": {"kind": "result", "en": "asks about the unclear comment instead of guessing", "zh": "看不懂的意見會問，不亂猜"},
    "no_performative_agreement": {"kind": "rule", "en": "no \"You're absolutely right!\" or \"Great point!\"", "zh": "不說「你完全正確！」「好觀點！」",
                                  "quote": "\"You're absolutely right!\"", "flag": PERFORM.pattern},
    "no_thanks": {"kind": "rule", "en": "no thanks of any kind", "zh": "不道謝", "quote": "ANY gratitude expression", "flag": THANKS.pattern},
}
