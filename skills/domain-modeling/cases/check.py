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
        "settled_terms": all(term.lower() in ent for term in e["avoid"]),
        "avoid_lists": all(all(w.lower() in avoid.get(term.lower(), "") for w in ws) for term, ws in e["avoid"].items()),
        "tight_definitions": bool(defs) and all(1 <= _sentences(d) <= 2 for d in defs.values()),
        "no_general_terms": not any(g.lower() in ent for g in e["general"]),
        "no_implementation_details": not re.search(r"`|(?i:\b(table|column|endpoint|database|foreign key|json|webhook|ttl)\b)", t),
    }
