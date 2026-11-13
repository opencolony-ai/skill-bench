#!/usr/bin/env python3
"""Which skills are worth benchmarking: a candidate list from the two places people install skills.

    python tools/candidates.py [--out candidates] [--plugins 50] [--skills 200]

Sources (fetched live; nothing here is a judgement):
  skills.sh             the leaderboard API behind https://skills.sh (installs reported by the `npx skills`
                        CLI's anonymous telemetry, on by default, off with DISABLE_TELEMETRY / DO_NOT_TRACK).
  Claude plugin directory  https://claude.com/marketplace/plugins (Anthropic's install count per plugin), and
                        `claude plugin list --available --json` for each plugin's source repository, whose
                        SKILL.md files are listed with git (no file contents are downloaded).

Cleaning, all by fixed rules a reader can check:
  recent     skills are ranked by installs in the last 8 weeks, not all-time (old bursts fade out).
  bundle     three or more skills of one repository whose 8-week installs are within 3% of each other were
             installed as a set; their counts are not separate votes.
  clone      repositories that share three or more skill names with another repository and move in lockstep
             with it (8-week installs within 3%): copies, kept in the list but flagged and not counted.
Use: a rough guess from the skill's name and description, so people can group skills into colonies; it is
meant to be corrected by hand. Gradable says whether a program can check the result without network, a
browser or a paid service.

Standard library only, plus the `git` command and (for plugin contents) the `claude` command.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

UA = {"User-Agent": "skill-bench-candidates/1 (+https://github.com/opencolony-ai/skill-bench)"}

USES = [  # (id, english, chinese, gradable by a program?, pattern on name + description)
    ("code-review", "Code review", "程式碼審查", True, r"review|reviewer|audit-code|code-quality|simplif"),
    ("git-commit-pr", "Commits and pull requests", "提交與 PR", True, r"commit|\bpr\b|pull-request|changelog|git\b|github-pr|release-note"),
    ("planning", "Planning and specs", "規劃與規格", True, r"plan|spec|prd|grill|brainstorm|design-doc|requirement|ticket|triage|wayfinder|architect"),
    ("testing", "Testing and TDD", "測試與 TDD", True, r"\btdd\b|test|qa\b|verification|verify"),
    ("debugging", "Debugging", "除錯", True, r"debug|diagnos|bug|root-cause|investigat"),
    ("frontend", "Front end and UI design", "前端與介面設計", True, r"frontend|front-end|\bui\b|ui-|ux|design|css|tailwind|shadcn|landing|web-design|taste|brand|theme"),
    ("writing", "Writing and docs", "寫作與文件", True, r"writ|doc|readme|copy|comms|newsletter|blog|summar|handoff|glossary|domain-model|teach|explain"),
    ("office", "Office files", "Office 文件", False, r"pptx|docx|xlsx|\bpdf\b|excel|word|powerpoint|slides|spreadsheet"),
    ("marketing", "Marketing and sales", "行銷與業務", True, r"market|seo|email|social|ads?\b|campaign|launch|sales|growth|cro\b|pricing|competitor|product-hunt|twitter|reddit|linkedin"),
    ("media", "Images, video and audio", "圖片、影片與聲音", False, r"video|image|audio|avatar|music|voice|thumbnail|photo|remotion|hyperframes|media|animation|gif|storyboard|seedance|p-video"),
    ("browser", "Browser and web automation", "瀏覽器與網路自動化", False, r"browser|playwright|scrap|crawl|web-search|search|automation|chrome|puppeteer"),
    ("framework", "Framework and language guides", "框架與語言指南", True, r"react|next|vue|svelte|angular|golang|go-|rust|python|typescript|swift|kotlin|django|rails|laravel|expo|flutter|node|fastapi|lsp"),
    ("cloud", "Cloud and DevOps", "雲端與 DevOps", False, r"azure|aws|gcp|cloud|kubernetes|k8s|docker|terraform|deploy|devops|cloudflare|infra"),
    ("data", "Data and databases", "資料與資料庫", True, r"data|sql|postgres|supabase|convex|database|analytics|pandas|csv|bigquery|db\b"),
    ("agent", "Agent tooling and skills about skills", "agent 工具與技能管理", True, r"skills?\b|prompt|memory|\bmcp\b|subagent|claude\.md|agents\.md|orchestrat|handoff|find-skills|\bloop\b"),
    ("security", "Security", "資安", True, r"secur|vuln|threat|pentest|owasp|secret"),
]


CACHE: Path | None = None   # --cache: keep fetched pages for a day, so a rerun is quick


def get(url: str, tries: int = 3) -> bytes:
    import hashlib
    f = CACHE / hashlib.sha256(url.encode()).hexdigest()[:32] if CACHE else None
    if f and f.is_file() and time.time() - f.stat().st_mtime < 86400:
        return f.read_bytes()
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            if f:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(data)
            return data
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError("unreachable")


def guess_use(name: str, desc: str = "") -> tuple[str, bool]:
    """The use whose words appear most: three points for each word in the name, one in the description."""
    n, d = name.lower().replace("_", "-"), desc.lower()
    best, score = ("other", False), 0
    for uid, _en, _zh, gradable, pat in USES:
        s = 3 * len(set(re.findall(pat, n))) + len(set(re.findall(pat, d)))
        if s > score:
            best, score = (uid, gradable), s
    return best


# ------------------------------------------------------------------ skills.sh

def skills_sh(pause: float = 0.5) -> tuple[list[dict], dict]:
    rows, page, meta = [], 0, {}
    while True:
        d = json.loads(get(f"https://www.skills.sh/api/skills/all-time/{page}"))
        rows += d.get("skills") or []
        meta = {"listed": d.get("total")}
        if not d.get("hasMore") or not d.get("skills"):
            break
        page += 1
        time.sleep(pause)
    seen, out = set(), []
    for s in rows:
        k = (s["source"], s["skillId"])
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out, meta


def _close(a: float, b: float, tol: float = 0.03) -> bool:
    return max(a, b) > 0 and abs(a - b) / max(a, b) <= tol


def flag_bundles_and_clones(rows: list[dict]) -> None:
    for s in rows:
        s["recent"] = sum(s.get("weeklyInstalls") or [])
        s["flags"] = []
    by_repo = collections.defaultdict(list)
    for s in rows:
        by_repo[s["source"]].append(s)
    for repo, ss in by_repo.items():               # bundle: three or more skills of a repo in lockstep
        for s in ss:
            mates = [o for o in ss if o is not s and _close(o["recent"], s["recent"])]
            if len(mates) >= 2:
                s["flags"].append("bundle")
    names = {repo: {s["skillId"] for s in ss} for repo, ss in by_repo.items() if len(ss) >= 3}
    for a, na in names.items():                    # clone: shares names with another repo and moves with it
        for b, nb in names.items():
            if a >= b or len(na & nb) < 3:
                continue
            shared = na & nb
            ra = {s["skillId"]: s["recent"] for s in by_repo[a]}
            rb = {s["skillId"]: s["recent"] for s in by_repo[b]}
            lock = sum(_close(ra[n], rb[n], 0.25) for n in shared)
            if lock >= 3 and not any(s.get("isOfficial") for s in by_repo[a] + by_repo[b]):
                for s in by_repo[a] + by_repo[b]:
                    if s["skillId"] in shared and "clone" not in s["flags"]:
                        s["flags"].append("clone")


# ------------------------------------------------------------------ Claude plugin directory

def plugin_directory() -> list[dict]:
    t = get("https://claude.com/marketplace/plugins").decode("utf-8", "replace").replace('\\"', '"')
    items = {}
    for m in re.finditer(r'"title":"((?:[^"\\]|\\.)*)","slug":"([^"]+)".{0,600}?"anthropicVerified":(true|false),'
                         r'"installs":(\d+|null)', t, re.S):
        title, slug, ver, inst = m.groups()
        if inst != "null":
            items[slug] = {"title": title, "slug": slug, "verified": ver == "true", "installs": int(inst)}
    return sorted(items.values(), key=lambda r: -r["installs"])


def plugin_sources() -> dict:
    """name -> {repo url, sha, description} from Claude Code's own listing of the directory."""
    claude = shutil.which("claude")
    if not claude:
        return {}
    try:
        p = subprocess.run([claude, "plugin", "list", "--available", "--json"], capture_output=True, text=True, timeout=300)
        av = json.loads(p.stdout).get("available") or []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}
    out = {}
    for a in av:
        src = a.get("source") or {}
        out[a["name"].lower()] = {"url": src.get("url") or (f"https://github.com/{src['repo']}" if src.get("repo") else None),
                                  "path": src.get("path"), "sha": src.get("sha"), "description": a.get("description", "")}
    return out


_TREES: dict[str, list[str]] = {}


def skills_in_repo(url: str, sha: str | None, sub: str | None) -> dict[str, str]:
    """{skill name: path of its SKILL.md} in a repository, listed without downloading file contents."""
    if url not in _TREES:
        _TREES[url] = _tree(url)
    prefix = (sub.strip("/") + "/") if sub else ""
    return {Path(f).parent.name: f for f in sorted(_TREES[url]) if f.endswith("SKILL.md") and f.startswith(prefix)}


def describe_skills_sh(source: str, skill: str) -> str:
    """The description skills.sh shows for a skill (its page's meta description)."""
    try:
        t = get(f"https://www.skills.sh/{source}/{skill}").decode("utf-8", "replace")
    except OSError:
        return ""
    m = re.search(r'<meta name="description" content="([^"]*)"', t)
    return html.unescape(m.group(1)) if m else ""


def describe_skill_md(url: str, sha: str | None, path: str) -> str:
    """The description in a SKILL.md's front matter, read from GitHub's raw file service."""
    repo = re.sub(r"^https://github.com/|\.git$", "", url or "")
    if not repo or "/" not in repo:
        return ""
    try:
        t = get(f"https://raw.githubusercontent.com/{repo}/{sha or 'HEAD'}/{path}").decode("utf-8", "replace")
    except OSError:
        return ""
    m = re.search(r"(?ms)^description:\s*(>-?|\|-?)?\s*(.+?)(?=^\w[\w-]*:|^---)", t)
    return re.sub(r"\s+", " ", m.group(2)).strip().strip('"') if m else ""


def _tree(url: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, tmp],
                           check=True, capture_output=True, timeout=180, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            files = subprocess.run(["git", "-C", tmp, "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True,
                                   text=True, timeout=60).stdout.splitlines()
        except (OSError, subprocess.SubprocessError):
            return []
    return files


# ------------------------------------------------------------------ the list

def build(n_plugins: int, n_skills: int) -> dict:
    rows, meta = skills_sh()
    flag_bundles_and_clones(rows)
    clones = sorted({s["source"] for s in rows if "clone" in s["flags"]})
    ranked = sorted(rows, key=lambda s: -s["recent"])
    candidates = {}
    for rank, s in enumerate(ranked, 1):
        if len(candidates) >= n_skills:
            break
        if "clone" in s["flags"]:
            continue
        desc = describe_skills_sh(s["source"], s["skillId"])
        time.sleep(0.2)
        use, gradable = guess_use(s["skillId"], desc)          # name and description; repo names mislead
        candidates[f"{s['source']}/{s['skillId']}"] = {
            "id": f"{s['source']}/{s['skillId']}", "name": s["skillId"], "repo": s["source"], "use": use, "description": desc,
            "gradable": gradable, "skills_sh": {"rank_recent": rank, "recent_8w": s["recent"], "all_time": s["installs"],
                                                "official": bool(s.get("isOfficial")), "flags": s["flags"]},
            "plugin": None}
    plugins = plugin_directory()
    sources = plugin_sources()
    plugin_rows = []
    for rank, p in enumerate(plugins[:n_plugins], 1):
        src = sources.get(p["slug"].lower()) or sources.get(p["title"].lower()) or {}
        inside = skills_in_repo(src["url"], src.get("sha"), src.get("path")) if src.get("url") else {}
        plugin_rows.append({**p, "rank": rank, "repo": src.get("url"), "skills": sorted(inside),
                            "description": src.get("description", "")})
        if not inside:  # commands, agents, hooks or an MCP server, no SKILL.md: listed as the plugin itself
            use, gradable = guess_use(p["slug"] + " " + p["title"], src.get("description", ""))
            candidates[f"plugin:{p['slug']}"] = {"id": f"plugin:{p['slug']}", "name": p["title"], "repo": src.get("url") or "",
                                                 "description": src.get("description", ""),
                                                 "use": use, "gradable": gradable, "kind": "plugin without skills",
                                                 "skills_sh": None, "plugin": {"name": p["title"], "rank": rank,
                                                 "installs": p["installs"], "verified": p["verified"]}}
        for name, path in inside.items():
            repo = re.sub(r"^https://github.com/|\.git$", "", src["url"] or "")
            key = f"{repo}/{name}"
            if key not in candidates:
                desc = describe_skill_md(src["url"], src.get("sha"), path)
                use, gradable = guess_use(name, desc)
                candidates[key] = {"id": key, "name": name, "repo": repo, "use": use, "gradable": gradable,
                                   "description": desc, "skills_sh": None, "plugin": None}
            c = candidates[key]
            c["plugin"] = {"name": p["title"], "rank": rank, "installs": p["installs"], "verified": p["verified"],
                           "skills_in_plugin": len(inside)}
    return {"fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "sources": {"skills_sh_listed": meta.get("listed"), "skills_sh_fetched": len(rows),
                        "plugins_with_installs": len(plugins), "plugins_examined": len(plugin_rows),
                        "clone_repos_left_out": clones},
            "uses": [{"id": u[0], "en": u[1], "zh": u[2], "gradable": u[3]} for u in USES] +
                    [{"id": "other", "en": "Other", "zh": "其他", "gradable": False}],
            "plugins": plugin_rows, "candidates": sorted(candidates.values(), key=_weight, reverse=True)}


def _weight(c: dict) -> float:
    """Recent skills.sh installs, plus plugin installs spread over the plugin's skills (a plugin installs them all)."""
    w = (c["skills_sh"] or {}).get("recent_8w") or 0
    if "bundle" in ((c["skills_sh"] or {}).get("flags") or []):
        w *= 0.5      # a set installed together: half weight, so one bundle cannot fill the list
    pl = c["plugin"] or {}
    # all-time plugin installs, shared among the plugin's skills (one install brings them all), roughly to 8 weeks' scale
    return w + (pl.get("installs") or 0) / 8 / max(1, pl.get("skills_in_plugin") or 1)


def markdown(d: dict) -> str:
    by_use = collections.defaultdict(list)
    for c in d["candidates"]:
        by_use[c["use"]].append(c)
    names = {u["id"]: u for u in d["uses"]}
    out = [f"# Candidate skills ({d['fetched'][:10]})", "",
           "Generated by `python tools/candidates.py`. Ranked by recent installs on skills.sh plus the Claude plugin "
           "directory's installs; see the script's docstring for the sources and the cleaning rules. The use is a guess "
           "from the name, to be corrected by hand.", "",
           f"skills.sh: {d['sources']['skills_sh_fetched']:,} skills on its leaderboard. Claude plugin directory: "
           f"{d['sources']['plugins_with_installs']} plugins with install counts, the top {d['sources']['plugins_examined']} "
           "opened to list their skills.", "",
           f"Left out as lockstep copies of each other ({len(d['sources']['clone_repos_left_out'])} repositories): "
           + ", ".join(f"`{r}`" for r in d["sources"]["clone_repos_left_out"]) + ".", "",
           "| Use | Candidates | Gradable by a program | Top skills |", "| --- | --- | --- | --- |"]
    order = sorted(by_use, key=lambda u: -len(by_use[u]))
    for u in order:
        cs = by_use[u]
        top = ", ".join(f"`{c['repo'].split('/')[-1]}/{c['name']}`" for c in cs[:6])
        out.append(f"| {names[u]['en']} ({names[u]['zh']}) | {len(cs)} | {'yes' if names[u]['gradable'] else 'no'} | {top} |")
    out += ["", "## Top 60", "", "| # | Skill | Use | skills.sh, last 8 weeks | Plugin installs | Flags |", "| --- | --- | --- | --- | --- | --- |"]
    for i, c in enumerate(d["candidates"][:60], 1):
        ss, pl = c["skills_sh"] or {}, c["plugin"] or {}
        out.append(f"| {i} | `{c['id']}` | {names[c['use']]['en']} | {ss.get('recent_8w', 0):,} | "
                   f"{(str(pl.get('installs', '')) + ' (' + pl.get('name', '') + ')') if pl else '-'} | {', '.join(ss.get('flags') or [])} |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="candidates")
    ap.add_argument("--plugins", type=int, default=50)
    ap.add_argument("--skills", type=int, default=200)
    ap.add_argument("--cache", help="folder to keep fetched pages in for a day")
    a = ap.parse_args()
    global CACHE
    CACHE = Path(a.cache) if a.cache else None
    d = build(a.plugins, a.skills)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "CANDIDATES.md").write_text(markdown(d), encoding="utf-8")
    print(f"wrote {out}/candidates.json and {out}/CANDIDATES.md: {len(d['candidates'])} candidates")


if __name__ == "__main__":
    main()
