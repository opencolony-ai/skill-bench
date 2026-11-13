"""The report: one card per skill (results, following the skill, cost, time), and for every case
what Claude wrote without and with the skill, side by side, with each check in plain words.

Built from results/ by `python bench.py site`. Standard library only; every piece of text from a
result is escaped, and pages Claude wrote are shown in sandboxed frames that run no script."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import bench

T = {
    "en": {
        "title": "skill-bench report", "lang_other": "中文", "other": "zh-TW.html",
        "intro": "Each skill's cases are done twice by Claude Code: without the skill and with it. A program grades the files "
                 "Claude wrote. Two kinds of checks, decided before anyone runs:",
        "kind_result": "Results: what the task itself asked for. Claude without the skill has a fair chance at these.",
        "kind_rule": "Follows the skill: rules the skill states, each quoting its sentence. Without the skill Claude was never "
                     "told them, so this shows the skill was read and obeyed, not that the work got better.",
        "verdict_rule": "The one-line verdict follows fixed rules: results first, then format, then cost.",
        "results": "Results", "rules": "Follows the skill", "cost": "Cost", "time": "Time", "out": "Output tokens",
        "used": "Claude opened the skill", "verifiers": "Verifiers", "without": "Without the skill", "with": "With the skill",
        "runs": "runs", "source": "source", "by": "by", "cases": "What Claude wrote, case by case", "task": "The task",
        "result_k": "result", "rule_k": "rule", "skill_says": "the skill says", "nothing": "(no file written)",
        "not_run": "Not run yet", "shown": "Shown: the run by {user} on {date}.", "nores": "no rule checks",
        "repo": "Repository and leaderboard",
    },
    "zh": {
        "title": "skill-bench 報告", "lang_other": "English", "other": "index.html",
        "intro": "每個技能的案例，Claude Code 做兩次：沒裝技能一次、裝了技能一次，再由程式評分 Claude 寫出的檔案。"
                 "檢查分兩種，跑之前就定好：",
        "kind_result": "結果：題目本身要求的事。沒裝技能的 Claude 也有公平的機會做到。",
        "kind_rule": "照技能做：技能自己規定的規則，每一條都引用技能的原句。沒裝技能的 Claude 根本不知道這些規則，"
                     "所以這只代表技能有被讀、被遵守，不代表做得更好。",
        "verdict_rule": "一句話結論照固定規則產生：先看結果，再看格式，最後看費用。",
        "results": "結果", "rules": "照技能做", "cost": "費用", "time": "時間", "out": "輸出 token",
        "used": "Claude 有打開技能", "verifiers": "驗證人數", "without": "沒裝技能", "with": "裝了技能",
        "runs": "次", "source": "來源", "by": "作者", "cases": "Claude 寫了什麼（逐題）", "task": "題目",
        "result_k": "結果", "rule_k": "規則", "skill_says": "技能原句", "nothing": "（沒有寫出檔案）",
        "not_run": "尚未有人驗證", "shown": "顯示的是 {user} 在 {date} 跑的那一次。", "nores": "沒有規則檢查",
        "repo": "Repository 與排行榜",
    },
}

CSS = """
:root{--bg:#fbfbf9;--fg:#1d1d1b;--mute:#6b6b66;--line:#dcdcd6;--ok:#17703a;--no:#b3261e;--card:#fff;--mark:#ffd9d6}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecece8;--mute:#a3a39c;--line:#3a3a36;--ok:#5cc489;--no:#ff8a80;--card:#1f1f1d;--mark:#5a2420}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}a{color:inherit}
h1{font-size:28px;margin:0 0 8px}.mute{color:var(--mute)}.top{display:flex;justify-content:space-between;gap:16px;align-items:baseline}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:16px 0}
.card h2{margin:0;font-size:20px}.verdict{font-size:18px;font-weight:600;margin:6px 0 12px}
.better{color:var(--ok)}.worse{color:var(--no)}
table.k{border-collapse:collapse;width:100%;max-width:640px}table.k td,table.k th{padding:4px 8px;border-bottom:1px solid var(--line);text-align:left;font-weight:normal}
table.k th{color:var(--mute);width:40%}
details{margin-top:12px}summary{cursor:pointer;font-weight:600}
.case{border-top:1px solid var(--line);margin-top:16px;padding-top:12px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:760px){.pair{grid-template-columns:1fr}}
.side h4{margin:4px 0;font-size:15px}pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--line);
border-radius:6px;padding:8px;font-size:13px;max-height:420px;overflow:auto;margin:6px 0}
iframe{width:100%;height:420px;border:1px solid var(--line);border-radius:6px;background:#fff}
mark{background:var(--mark);color:inherit}ul.ch{list-style:none;padding:0;margin:6px 0;font-size:14px}
ul.ch li{margin:2px 0}.y{color:var(--ok)}.n{color:var(--no);font-weight:600}.kind{font-size:12px;color:var(--mute);border:1px solid var(--line);
border-radius:4px;padding:0 4px;margin-right:4px}.q{display:block;font-size:12px;color:var(--mute);margin-left:22px}
.fn{font-size:12px;color:var(--mute);margin:8px 0 0}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def _marked(text: str, patterns: list[str]) -> str:
    """Escape text, wrapping what the failed rules point at in <mark>."""
    spans = []
    for p in patterns:
        try:
            spans += [(m.start(), m.end()) for m in re.finditer(p, text) if m.end() > m.start()]
        except re.error:
            pass
    spans.sort()
    out, at = [], 0
    for a, b in spans:
        if a < at:
            continue
        out += [esc(text[at:a]), "<mark>", esc(text[a:b]), "</mark>"]
        at = b
    out.append(esc(text[at:]))
    return "".join(out)


def _side(label: str, arm: dict, case, about: dict, w: dict) -> str:
    c = (arm.get("cases") or {}).get(case.name) or {}
    got = c.get("checks") or {}
    failed_flags = [about[k]["flag"] for k, v in got.items() if not v and about.get(k, {}).get("flag")]
    files = []
    for fn, text in (c.get("outputs") or {}).items():
        if text is None:
            continue
        if fn.lower().endswith((".html", ".htm")):
            body = f'<iframe sandbox="" referrerpolicy="no-referrer" loading="lazy" title="{esc(fn)}" srcdoc="{esc(text)}"></iframe>'
        else:
            body = f"<pre>{_marked(text, failed_flags)}</pre>"
        files.append(f'<div class="fn">{esc(fn)}</div>{body}')
    items = []
    for kind in ("result", "rule"):
        for k, v in got.items():
            a = about.get(k, {"kind": "result", "en": k, "zh": k})
            if a["kind"] != kind or k == "checker_ran" and v:
                continue
            q = f'<span class="q">{esc(w["skill_says"])}: “{esc(a["quote"])}”</span>' if a.get("quote") and not v else ""
            items.append(f'<li class="{"y" if v else "n"}">{"✓" if v else "✗"} <span class="kind">{esc(w[kind + "_k"])}</span>'
                         f'{esc(a["zh"] if w is T["zh"] else a["en"])}{q}</li>')
    return (f'<div class="side"><h4>{esc(label)}</h4>{"".join(files) or esc(w["nothing"])}'
            f'<ul class="ch">{"".join(items)}</ul></div>')


def _card(name: str, w: dict, lang: str) -> str:
    s = bench.standing(name)
    meta = bench.skill_meta(name)
    src = meta.get("source")
    head = (f'<h2 id="{esc(name)}">{esc(name)}</h2><div class="mute">{esc(w["by"])} {esc(meta["author"])}'
            + (f' · <a href="{esc(src)}">{esc(w["source"])}</a>' if src else "") + "</div>")
    if "verdict" not in s:
        return f'<section class="card">{head}<div class="verdict mute">{esc(w["not_run"])}</div></section>'
    n = s["cases"]
    frac = lambda x: f"{x:g}/{n}"
    rows = [(w["results"], bench._arrow(s, "result", frac)),
            (w["rules"], bench._arrow(s, "rule", frac) if s.get("rule_none") is not None else w["nores"]),
            (w["cost"], bench._arrow(s, "cost", lambda x: f"${x:.2f}") + (f" ({s['cost_change']:+d}%)" if s.get("cost_change") is not None else "")),
            (w["time"], bench._arrow(s, "seconds", lambda x: f"{x:.0f} s")),
            (w["out"], bench._arrow(s, "output_tokens", lambda x: f"{x:,.0f}")),
            (w["used"], f"{s['used']}/{s['verifiers']} {w['runs']}"),
            (w["verifiers"], f"{s['verifiers']}/{bench.NEED} · {bench.STATUS_WORDS[s['status']]}")]
    table = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows)
    table = f'<table class="k"><tr><th></th><td class="mute">{esc(w["without"])} → {esc(w["with"])}</td></tr>{table}</table>'
    # the run shown: the latest of those counted
    runs = [r for r in bench.load_results(name) if r.get("version") == s["version"]
            and str(r.get("user", "")).lower() in s["users"]]
    run = max(runs, key=lambda r: r.get("finished", ""))
    abouts = bench._abouts(name)
    cases = []
    for c in bench.case_dirs(name):
        task = (c / "task.md").read_text(encoding="utf-8")
        cases.append(f'<div class="case"><details><summary>{esc(c.name)} · {esc(w["task"])}</summary><pre>{esc(task)}</pre></details>'
                     f'<div class="pair">{_side(w["without"], run["arms"]["none"], c, abouts[c.name], w)}'
                     f'{_side(w["with"], run["arms"]["skill"], c, abouts[c.name], w)}</div></div>')
    shown = w["shown"].format(user=run.get("user", "?"), date=str(run.get("finished", ""))[:10])
    cls = s["verdict"] if s["verdict"] in ("better", "worse") else ""
    return (f'<section class="card">{head}<div class="verdict {cls}">{esc(bench.verdict_text(s, lang))}</div>{table}'
            f'<details><summary>{esc(w["cases"])}</summary><p class="mute">{esc(shown)}</p>{"".join(cases)}</details></section>')


def page(lang: str) -> str:
    w = T[lang]
    names = bench.skill_names()
    order = {"better": 0, "worse": 1, "format": 2, "none": 3}
    st = {n: bench.standing(n) for n in names}
    names.sort(key=lambda n: ("verdict" not in st[n], order.get(st[n].get("verdict"), 9), n))
    cards = "".join(_card(n, w, lang) for n in names)
    return (f'<!doctype html><html lang="{"zh-Hant" if lang == "zh" else "en"}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(w["title"])}</title>'
            f'<style>{CSS}</style></head><body><main><div class="top"><h1>{esc(w["title"])}</h1>'
            f'<a href="{esc(w["other"])}">{esc(w["lang_other"])}</a></div>'
            f'<p>{esc(w["intro"])}</p><ul><li>{esc(w["kind_result"])}</li><li>{esc(w["kind_rule"])}</li></ul>'
            f'<p class="mute">{esc(w["verdict_rule"])} <a href="https://github.com/opencolony-ai/skill-bench">{esc(w["repo"])}</a></p>'
            f'{cards}</main></body></html>\n')


# ------------------------------------------------------------------ the colony dashboard's data

POINTS = {"verification": 1, "pioneer": 1, "agreement": 2}
POINTS_RULE = {
    "en": ["+1 for every verification CI accepted (it cost you real money).",
           "+1 for being one of the first three verifiers of a skill version.",
           "+2 when three or more people have verified that version and your run agrees with the median within one case."],
    "zh": ["每一次被 CI 接受的驗證 +1（你真的花了錢）。",
           "是某技能某版本的前三位驗證者，開路 +1。",
           "那個版本有三人以上驗證，而且你的結果和中位數差不到一題，一致 +2。"],
}


def colonies() -> list[dict]:
    """colonies.json: each colony is a set of skills for one use; a skill not listed lands in "other"."""
    f = bench.ROOT / "colonies.json"
    cs = json.loads(f.read_text(encoding="utf-8"))["colonies"] if f.is_file() else []
    listed = {s for c in cs for s in c["skills"]}
    rest = [n for n in bench.skill_names() if n not in listed]
    if rest:
        cs.append({"id": "other", "name": {"en": "Other", "zh": "其他"}, "about": {"en": "", "zh": ""}, "skills": rest})
    known = set(bench.skill_names())
    return [{**c, "skills": [s for s in c["skills"] if s in known]} for c in cs]


def points() -> dict:
    """Points per person, computed only from results/ (anyone can recompute them). Older versions of a
    skill still count for the work done; agreement is judged within each version."""
    out: dict[str, dict] = {}
    by_version: dict[tuple, list] = {}
    for r in bench.load_results():
        name, user = r.get("skill"), str(r.get("user", "")).lower()
        if not user or name not in bench.skill_names() or user == bench.skill_meta(name)["author"].lower():
            continue
        if bench.passes(r, "none") is None or bench.passes(r, "skill") is None:
            continue
        by_version.setdefault((name, r.get("version")), []).append(r)
    for (name, ver), rs in by_version.items():
        latest = {}
        for r in sorted(rs, key=lambda r: r.get("finished", "")):
            latest[str(r["user"]).lower()] = r          # one result per person per version
        order = sorted(latest.values(), key=lambda r: r.get("finished", ""))
        a = [bench.passes(r, "none") for r in order]
        b = [bench.passes(r, "skill") for r in order]
        enough = len(order) >= bench.NEED
        ma, mb = (bench.statistics.median(a), bench.statistics.median(b)) if order else (0, 0)
        for i, r in enumerate(order):
            u = str(r["user"]).lower()
            w = out.setdefault(u, {"user": r["user"], "verifications": 0, "points": 0, "agreed": 0, "pending": 0,
                                   "skills": [], "last": "", "spent_usd": 0.0})
            w["verifications"] += 1
            w["points"] += POINTS["verification"] + (POINTS["pioneer"] if i < bench.NEED else 0)
            agrees = abs(a[i] - ma) <= bench.TOLERANCE and abs(b[i] - mb) <= bench.TOLERANCE
            if enough and agrees:
                w["points"] += POINTS["agreement"]
                w["agreed"] += 1
            elif not enough:
                w["pending"] += 1
            if name not in w["skills"]:
                w["skills"].append(name)
            w["last"] = max(w["last"], str(r.get("finished", "")))
            w["spent_usd"] += sum((r["arms"][arm].get("usage") or {}).get("cost_usd") or 0 for arm in bench.ARMS)
    return out


def colony_data() -> dict:
    """Everything the colony dashboard draws, in one file. It has no state of its own."""
    import datetime as dt
    workers = sorted(points().values(), key=lambda w: (-w["points"], w["user"].lower()))
    cs, skills_total, with_results, consensus, runs = [], 0, 0, 0, 0
    for c in colonies():
        items = []
        for name in c["skills"]:
            s, meta = bench.standing(name), bench.skill_meta(name)
            skills_total += 1
            item = {"name": name, "author": meta["author"], "source": meta.get("source"), "cases": s["cases"],
                    "version": s["version"], "verifiers": s["verifiers"], "need": bench.NEED, "status": s["status"],
                    "users": s["users"], "claims": [], "report": f"index.html#{name}"}
            if "verdict" in s:
                with_results += 1
                consensus += s["status"] in ("consistent", "no signal")
                item.update(verdict=s["verdict"], verdict_text={l: bench.verdict_text(s, l) for l in ("en", "zh")},
                            used=s["used"], cost_change=s.get("cost_change"),
                            **{k: [s.get(f"{k}_none"), s.get(f"{k}_skill")] for k in ("result", "rule", "cost", "seconds")})
            items.append(item)
        cs.append({**c, "skills": items})
    for r in bench.load_results():
        runs += 1
    spent = sum(w["spent_usd"] for w in workers)
    return {"schema": 1, "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "need": bench.NEED, "points_rule": POINTS_RULE,
            "totals": {"skills": skills_total, "with_results": with_results, "consensus": consensus,
                       "workers": len(workers), "verifications": runs, "spent_usd": round(spent, 2), "active_claims": 0},
            "colonies": cs, "workers": workers}


def build(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = []
    (out / "colony.json").write_text(json.dumps(colony_data(), ensure_ascii=False, indent=1), encoding="utf-8")
    files.append(out / "colony.json")
    dash = bench.ROOT / "web" / "colony.html"
    if dash.is_file():
        (out / "colony.html").write_text(dash.read_text(encoding="utf-8"), encoding="utf-8")
        files.append(out / "colony.html")
    for lang, fn in (("en", "index.html"), ("zh", "zh-TW.html")):
        (out / fn).write_text(page(lang), encoding="utf-8")
        files.append(out / fn)
    return files


if __name__ == "__main__":
    print(json.dumps([str(p) for p in build(Path("site"))]))
