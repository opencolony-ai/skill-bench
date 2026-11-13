"""GLOSSARY.md in the format of domain-modeling's GLOSSARY-FORMAT.md: a context title and description,
a Language section, `**Term**:` entries of one or two sentences with `_Avoid_:` synonyms, the terms
the team settled on, no general programming concepts and no implementation details."""
import re


def _entries(t):
    out, cur = {}, None
    for line in t.splitlines():
        m = re.match(r"^\*\*([^*]+)\*\*:\s*(.*)$", line.strip())
        if m:
            cur = m.group(1).strip().lower()
            out[cur] = [m.group(2)] if m.group(2) else []
        elif line.startswith("#"):
            cur = None
        elif cur is not None and line.strip():
            out[cur].append(line.strip())
    return out


def _sentences(s):
    return len([x for x in re.split(r"(?<=[.!?])\s+", s.strip()) if x.strip()])


def check(folder, e):
    p = folder / "GLOSSARY.md"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    lines = [l for l in t.splitlines() if l.strip()]
    ent = _entries(t)
    avoid = {k: " ".join(l for l in v if l.startswith("_Avoid_")).lower() for k, v in ent.items()}
    defs = {k: " ".join(l for l in v if not l.startswith("_Avoid_")) for k, v in ent.items()}
    return {
        "exists": True,
        "context_title": bool(lines) and lines[0].startswith("# ") and len(lines) > 1 and not lines[1].startswith("#"),
        "language_section": bool(re.search(r"(?m)^## Language\s*$", t)),
        "term_entries": len(ent) >= 3,
        # any layout counts here: "**Shipment**:", "- **Shipment** -", "| Shipment |", "### Shipment"
        "settled_terms_defined": all(re.search(rf"(?im)^\s*(?:[-*]\s+|\|\s*|#+\s*)?(?:\*\*|__)?{re.escape(term)}s?(?:\*\*|__)?\s*(?:[:|\u2014\u2013-]|$)", t)
                                     for term in e["avoid"]),
        "avoid_lists": all(all(w.lower() in avoid.get(term.lower(), "") for w in ws) for term, ws in e["avoid"].items()),
        "tight_definitions": bool(defs) and all(1 <= _sentences(d) <= 2 for d in defs.values()),
        "no_general_terms": not any(g.lower() in ent for g in e["general"]),
        "no_implementation_details": not re.search(IMPL, t),
    }


IMPL = r"`|(?i:\b(table|column|endpoint|database|foreign key|json|webhook|ttl)\b)"


def _rule(en, zh, quote, flag=None):
    return {"kind": "rule", "en": en, "zh": zh, "quote": quote, **({"flag": flag} if flag else {})}


ABOUT = {
    "settled_terms_defined": {"kind": "result", "en": "defines each term the team settled on, in any layout",
                              "zh": "團隊定下的每個詞都有定義（版面不拘）"},
    "context_title": _rule("a context title and a one-line description", "情境標題加一句說明", "# {Context Name}"),
    "language_section": _rule("a ## Language section", "有 ## Language 一節", "## Language"),
    "term_entries": _rule("entries written **Term**: then the definition", "條目寫成 **詞**: 再接定義", "**Invoice**:"),
    "avoid_lists": _rule("rejected synonyms listed under _Avoid_:", "被捨棄的同義詞列在 _Avoid_: 底下", "_Avoid_: Bill, payment request"),
    "tight_definitions": _rule("definitions of one or two sentences", "定義一到兩句", "One or two sentences max"),
    "no_general_terms": _rule("no general programming terms (retry, cache ...)", "不收一般程式概念（retry、cache…）",
                              "General programming concepts (timeouts, error types, utility patterns) don't belong"),
    "no_implementation_details": _rule("no implementation details (tables, endpoints, code)", "不含實作細節（資料表、端點、程式碼）",
                                       "totally devoid of implementation details", IMPL),
}
