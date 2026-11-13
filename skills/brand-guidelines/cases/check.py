"""Anthropic's palette and typography from brand-guidelines' SKILL.md, checked on index.html: every
colour in the CSS is a brand colour, headings are Poppins (Arial fallback), body text Lora (Georgia
fallback)."""
import re

PALETTE = {"#141413", "#faf9f5", "#b0aea5", "#e8e6dc", "#d97757", "#6a9bcc", "#788c5d"}
RGB = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in PALETTE}
NAMED = r"white|black|gray|grey|silver|red|orange|blue|green|navy|teal|beige|ivory|whitesmoke|gainsboro|tan|brown"


def _css(t):
    parts = re.findall(r"(?is)<style[^>]*>(.*?)</style>", t) + re.findall(r'(?is)\sstyle\s*=\s*"([^"]*)"', t)
    return "\n".join(parts)


def _hex(h):
    h = h.lower()
    return "#" + "".join(c * 2 for c in h[1:4]) if len(h) in (4, 5) else h[:7]


def _resolve(css):
    var = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", css))
    for _ in range(3):
        css = re.sub(r"var\((--[\w-]+)(?:,[^)]*)?\)", lambda m: var.get(m.group(1), m.group(0)), css)
    return css


def _family_for(css, selector_word):
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        names = [s.strip().lower() for s in sel.split(",")]
        if any(re.fullmatch(rf"(.*\s)?{selector_word}", n) for n in names):
            m = re.search(r"font-family\s*:\s*([^;]+)", body)
            if m:
                return [f.strip().strip("'\"").lower() for f in m.group(1).split(",")]
    return []


def check(folder, e):
    p = folder / "index.html"
    if not p.is_file():
        return {"exists": False}
    t = p.read_text(encoding="utf-8")
    css = _resolve(_css(t))
    hexes = {_hex(h) for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", css)}
    rgbs = [tuple(int(x) for x in m) for m in re.findall(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css)]
    named = re.findall(rf"(?i)(?:color|background(?:-color)?|border(?:-[a-z]+)?|fill|stroke|outline)\s*:[^;]*\b({NAMED})\b", css)
    h1, body = _family_for(css, "h1"), _family_for(css, "body")
    return {
        "exists": True,
        "brand_colours_only": hexes <= PALETTE and all(c in RGB for c in rgbs) and not named,
        "uses_the_palette": len(hexes & PALETTE) + len(set(rgbs) & RGB) >= 3,
        "heading_font": h1[:1] == ["poppins"] and "arial" in h1,
        "body_font": body[:1] == ["lora"] and "georgia" in body,
        "content": all(s.lower() in t.lower() for s in e["text"]),
    }
