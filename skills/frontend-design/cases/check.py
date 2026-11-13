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


ABOUT = {
    "content": {"kind": "result", "en": "a page for the brief, with its content", "zh": "照題目內容做出頁面"},
    "no_all_caps_labels": {"kind": "rule", "en": "no all-caps labels", "zh": "沒有全大寫的小標", "quote": "Using all caps for labels.",
                           "flag": r"(?i)text-transform\s*:\s*uppercase"},
    "no_arrow_suffix": {"kind": "rule", "en": "no → on links and buttons", "zh": "連結和按鈕不加 →", "quote": "appended to link and button text",
                        "flag": r"→|&rarr;"},
    "no_middot_meta": {"kind": "rule", "en": "no 'A · B · C' meta strings", "zh": "沒有「A · B · C」式的資訊串", "quote": "meta strings joined with middle dots",
                       "flag": r"\s(·|&middot;)\s"},
    "no_default_palette": {"kind": "rule", "en": "not the cream / terracotta / near-black defaults", "zh": "沒用米色、赤陶色、近黑色這些預設色",
                           "quote": "a warm cream background (near #F4F1EA)"},
    "no_default_shadow": {"kind": "rule", "en": "not the soft grey card shadow", "zh": "沒用預設的淡灰卡片陰影", "quote": "the same soft grey shadow (rgba(0,0,0,.1))"},
    "keyboard_focus": {"kind": "rule", "en": "visible keyboard focus", "zh": "鍵盤焦點看得見", "quote": "visible keyboard focus"},
    "reduced_motion": {"kind": "rule", "en": "respects reduced motion when anything moves", "zh": "有動畫時尊重「減少動態」設定", "quote": "reduced motion respected"},
    "responsive": {"kind": "rule", "en": "works down to phone width", "zh": "手機寬度也能用", "quote": "responsive down to mobile"},
}
