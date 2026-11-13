"""The tells and the quality floor that frontend-design's SKILL.md names, checked on index.html.
Tells (avoid unless the brief asks): all-caps labels, '→' on links and buttons, meta strings joined
with ' · ', the cream / terracotta / tinted-near-black defaults, the soft grey card shadow. Floor:
visible keyboard focus, reduced motion respected when anything moves, responsive."""
import re

DEFAULTS = [(0xF4, 0xF1, 0xEA), (0xD9, 0x77, 0x57), (0x0B, 0x0B, 0x0B), (0x11, 0x11, 0x11)]


def _near(rgb):
    return any(sum(abs(a - b) for a, b in zip(rgb, d)) <= 10 for d in DEFAULTS)


def _rgb(h):
    h = h[1:]
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def check(folder, e):
    p = folder / "index.html"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    css = "\n".join(re.findall(r"(?is)<style[^>]*>(.*?)</style>", t) + re.findall(r'(?is)\sstyle\s*=\s*"([^"]*)"', t))
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    moves = re.search(r"(?i)\b(transition|animation)\s*:|@keyframes", css)
    return {
        "exists": True,
        "no_all_caps_labels": not re.search(r"(?i)text-transform\s*:\s*uppercase", css),
        "no_arrow_suffix": "→" not in t and "&rarr;" not in t and "\\2192" not in css,
        "no_middot_meta": not re.search(r"\S\s+(·|&middot;|&#183;)\s+\S", text),
        "no_default_palette": not any(_near(_rgb(h)) for h in re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css)),
        "no_default_shadow": not re.search(r"rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.10?\s*\)", css),
        "keyboard_focus": bool(re.search(r":focus(-visible)?\b", css)),
        "reduced_motion": not moves or "prefers-reduced-motion" in css,
        "responsive": bool(re.search(r"@media[^{]*(max|min)-width", css)) or bool(re.search(r"clamp\(|minmax\(|auto-fit|auto-fill", css)),
        "content": all(s.lower() in t.lower() for s in e["text"]),
    }
