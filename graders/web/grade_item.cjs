#!/usr/bin/env node
// Grades one front-end exam item: the output folder Claude wrote, against the item's _bench/item.json.
//
//   node grade_item.cjs <item-dir> <output-dir> <work-dir>
//
// Prints one JSON object: {layer1, brief, fixtures, motion, behaviour, review, reference, shots}. Every
// value is something a program measured; nothing here is a judgement. Judge questions in item.json
// (layers 2 and 3) are answered later by the judging schedule from the screenshots written to <work-dir>.
"use strict";
const fs = require("fs");
const path = require("path");
let chromium;
try { ({ chromium } = require("playwright")); } catch (e) { ({ chromium } = require("@playwright/test")); }
const { measure, axe, focusVisible, WIDTHS } = require("./render.cjs");

const MOTION_PROPS = new Set(["transform", "opacity", "clip-path", "translate", "scale", "rotate", "filter", "visibility"]);

function offline(context, log) {
  return context.route("**/*", (r) => {
    const u = r.request().url();
    if (/^(file|data|blob):/.test(u)) return r.continue();
    if (log && !log.includes(u)) log.push(u);
    return r.abort();
  });
}

async function openPage(browser, url, opts = {}) {
  const context = await browser.newContext({ viewport: { width: opts.width || 1280, height: (opts.width || 1280) < 700 ? 740 : 900 },
    deviceScaleFactor: 1, reducedMotion: opts.reducedMotion || "no-preference" });
  await offline(context, opts.external);
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 200)); });
  const t0 = Date.now();
  await page.goto(url, { waitUntil: "load", timeout: 30000 });
  const loadMs = Date.now() - t0;
  await page.waitForTimeout(opts.settle ?? 900);
  return { context, page, errors, loadMs };
}

// ------------------------------------------------------------------ layer 1 on the main page

async function layer1(browser, url, work) {
  const external = [], widths = {};
  let errors = [], reduced = null;
  for (const width of WIDTHS) {
    const { context, page, errors: e } = await openPage(browser, url, { width, external });
    const own = e.slice();        // the page's own errors; axe-core's own requests come after and are not the page's
    const m = await measure(page, width);
    m.axe = await axe(page);
    await page.screenshot({ path: path.join(work, `full-${width}.png`), fullPage: true });
    await page.screenshot({ path: path.join(work, `first-${width}.png`) });
    if (width === 1280) { m.focus = await focusVisible(page); errors = own; }
    widths[width] = m;
    await context.close();
  }
  {
    const { context, page } = await openPage(browser, url, { reducedMotion: "reduce", settle: 600 });
    reduced = await page.evaluate(() => {
      const a = document.getAnimations().filter((x) => x.playState === "running");
      return a.filter((x) => { const t = x.effect && x.effect.getComputedTiming(); return t && (t.iterations === Infinity || t.activeDuration > 1000); }).length;
    });
    await context.close();
  }
  const w = widths;
  const checks = {
    no_side_scroll_320: !w[320].sideScroll,
    no_overlapping_text: WIDTHS.every((x) => w[x].overlaps === 0),
    no_clipped_text: WIDTHS.every((x) => w[x].clipped === 0),
    no_serious_a11y: WIDTHS.every((x) => w[x].axe.byImpact.critical + w[x].axe.byImpact.serious === 0),
    focus_visible: !!w[1280].focus && w[1280].focus.visible === w[1280].focus.tabbed,   // nothing to tab to: nothing to check
    still_under_reduced_motion: reduced === 0,
    offline: external.length === 0,
    no_script_errors: errors.length === 0,
  };
  return { checks, pass: Object.values(checks).every(Boolean),
           detail: { widths: w, external, errors, endlessUnderReducedMotion: reduced,
                     tapTargetsSmall320: w[320].smallTargets, tinyText: w[320].tinyText, lineLength: w[1280].lineLengthMedian } };
}

// ------------------------------------------------------------------ layer 2: what the brief asked, by program

async function brief(browser, url, must) {
  const { context, page } = await openPage(browser, url, { width: 1280 });
  const text = (await page.evaluate(() => document.body.innerText || "")).replace(/\s+/g, " ");
  const low = text.toLowerCase();
  const out = {};
  for (const m of must || []) {
    if (m.text_any) out[m.id] = m.text_any.some((t) => low.includes(t.toLowerCase()));
    else if (m.text_all) out[m.id] = m.text_all.every((t) => low.includes(t.toLowerCase()));
    else if (m.no_text_any) out[m.id] = !m.no_text_any.some((t) => low.includes(t.toLowerCase()));
    else if (m.selector) out[m.id] = (await page.locator(m.selector).count()) >= (m.min ?? 1);
    else if (m.min_font_px) out[m.id] = await page.evaluate((px) => {
      // the running text people read: paragraphs, list items, labels, table cells, inputs
      const els = [...document.querySelectorAll("p,li,label,td,th,dd,input,select,textarea,button")]
        .filter((el) => el.getBoundingClientRect().width > 0 && (el.innerText || el.value || "").trim().length > 0);
      const sizes = els.map((el) => parseFloat(getComputedStyle(el).fontSize)).sort((a, b) => a - b);
      return sizes.length > 0 && sizes[Math.floor(sizes.length * 0.1)] >= px - 0.5;   // 90% of it at least px
    }, m.min_font_px);
    else if (m.palette) out[m.id] = await page.evaluate((pal) => {
      const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
      const P = pal.map(hex);
      const near = (rgb) => P.some((q) => Math.hypot(q[0] - rgb[0], q[1] - rgb[1], q[2] - rgb[2]) <= 8);
      const bad = new Set();
      for (const el of [document.documentElement, document.body, ...document.body.querySelectorAll("*")]) {
        const r = el.getBoundingClientRect(), s = getComputedStyle(el);
        if (el !== document.documentElement && el !== document.body && (r.width === 0 || s.visibility === "hidden" || s.display === "none")) continue;
        const props = [s.backgroundColor, s.borderTopWidth !== "0px" ? s.borderTopColor : null];
        if ([...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) props.push(s.color);
        for (const c of props) {
          if (!c) continue;
          const m = c.match(/rgba?\(([^)]+)\)/);
          if (!m) continue;
          const v = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
          if (v.length > 3 && v[3] === 0) continue;            // transparent
          if (!near(v.slice(0, 3))) bad.add(c);
        }
      }
      return bad.size === 0;
    }, m.palette);
  }
  out.no_placeholder_text = !/lorem ipsum|john doe|jane doe|\[object object\]|\bundefined\b|\bNaN\b/i.test(text);
  await context.close();
  return out;
}

// ------------------------------------------------------------------ states: the same page on hidden data

async function fixtures(browser, outDir, itemDir, page, list) {
  const res = {};
  for (const f of list || []) {
    const tmp = fs.mkdtempSync(path.join(require("os").tmpdir(), "fx-"));
    fs.cpSync(outDir, tmp, { recursive: true });
    fs.copyFileSync(path.join(itemDir, "_bench", f.src), path.join(tmp, f.file));
    const url = "file://" + path.join(tmp, page);
    const r = { };
    for (const width of [320, 1280]) {
      const { context, page: p, errors, loadMs } = await openPage(browser, url, { width, settle: 500 });
      const m = await measure(p, width);
      const text = (await p.evaluate(() => document.body.innerText || "")).replace(/\s+/g, " ");
      r[width] = { sideScroll: m.sideScroll, pastEdge: m.pastEdge, clipped: m.clipped, overlaps: m.overlaps, errors: errors.length, loadMs };
      if (width === 1280) {
        r.text_ok = !f.expect_text_any || f.expect_text_any.some((t) => text.toLowerCase().includes(t.toLowerCase()));
        r.no_junk = !/\bundefined\b|\bnull\b|\bNaN\b|\[object Object\]|Invalid Date/.test(text);
        if (f.no_text_any) r.text_ok = r.text_ok && !f.no_text_any.some((t) => text.includes(t));
      }
      await context.close();
    }
    const holds = !r[320].sideScroll && r[320].overlaps === 0 && r[1280].overlaps === 0 && r[320].clipped === 0 &&
      r[320].errors === 0 && r[1280].errors === 0 && r.text_ok && r.no_junk && (!f.max_ms || r[1280].loadMs <= f.max_ms);
    res[f.id] = { holds, ...r };
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  return res;
}

// ------------------------------------------------------------------ motion: open each control, read what animates

async function doSteps(page, steps) {
  for (const s of steps) {
    if (s.click) await page.click(s.click, { timeout: 3000 });
    else if (s.press) await page.keyboard.press(s.press);
    else if (s.hover) await page.hover(s.hover, { timeout: 3000 });
    else if (s.focus) await page.focus(s.focus, { timeout: 3000 });
    else if (s.wait) await page.waitForTimeout(s.wait);
  }
}

async function readAnimations(page, watch) {
  return page.evaluate((watch) => {
    const roots = [...document.querySelectorAll(watch)];
    const inside = (t) => t && roots.some((r) => r === t || r.contains(t));
    return document.getAnimations().filter((a) => a.effect && inside(a.effect.target)).map((a) => {
      const t = a.effect.getTiming(), kf = a.effect.getKeyframes ? a.effect.getKeyframes() : [];
      const props = new Set();
      for (const k of kf) for (const p of Object.keys(k)) if (!["offset", "computedOffset", "easing", "composite"].includes(p)) props.add(p.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase()));
      if (a.transitionProperty) props.add(a.transitionProperty);
      const first = kf.find((k) => (k.computedOffset ?? k.offset) === 0) || kf[0] || {};
      const easing = [t.easing, ...kf.map((k) => k.easing)].filter((e) => e && e !== "linear");
      return { duration: typeof t.duration === "number" ? t.duration : 0, delay: t.delay || 0, easing: easing[0] || "linear",
               props: [...props], startTransform: String(first.transform || first.scale || "") };
    }).filter((x) => x.duration > 1);
  }, watch);
}

const easeIn = (e) => /^ease-in$/.test(e) || /cubic-bezier\(\s*0?\.4\d*\s*,\s*0\s*,\s*1\s*,\s*1\s*\)/.test(e);
const fromZero = (t) => /scale\(\s*0(\.0+)?\s*[,)]|matrix\(\s*0(\.0+)?\s*,\s*0(\.0+)?\s*,\s*0(\.0+)?\s*,\s*0(\.0+)?\s*,|^0(\.0+)?$/.test(t.trim());

async function motion(browser, url, list) {
  const res = {};
  for (const it of list || []) {
    const r = {};
    for (const mode of ["no-preference", "reduce"]) {
      const { context, page } = await openPage(browser, url, { width: 1280, reducedMotion: mode, settle: 600 });
      try {
        await doSteps(page, it.steps.slice(0, -1));
        await page.waitForTimeout(100);
        const last = it.steps[it.steps.length - 1];
        await doSteps(page, [last]);
        await page.waitForTimeout(16);
        r[mode] = await readAnimations(page, it.watch);
      } catch (e) {
        r[mode] = { error: String(e).slice(0, 160) };
      }
      await context.close();
    }
    const a = Array.isArray(r["no-preference"]) ? r["no-preference"] : null;
    const red = Array.isArray(r["reduce"]) ? r["reduce"] : null;
    const moves = (x) => x.props.some((p) => !["opacity", "visibility", "filter"].includes(p));
    let holds;
    if (!a || !red) holds = false;
    else if (it.expect === "still") holds = a.length === 0;
    else holds = a.length > 0 &&
      a.every((x) => x.duration + x.delay <= (it.max_ms || 300)) &&
      a.every((x) => !easeIn(x.easing)) &&
      a.every((x) => x.props.every((p) => MOTION_PROPS.has(p))) &&
      a.every((x) => !fromZero(x.startTransform)) &&
      red.every((x) => !moves(x));
    res[it.id] = { holds, expect: it.expect, animations: a, reduced: red, error: (r["no-preference"] || {}).error || (r["reduce"] || {}).error };
  }
  return res;
}

// ------------------------------------------------------------------ improve: behaviour that must keep working

async function behaviour(browser, url, list) {
  const res = {};
  for (const b of list || []) {
    const { context, page, errors } = await openPage(browser, url, { width: 1280, settle: 300 });
    let ok = false, note = "";
    try {
      await doSteps(page, b.steps || []);
      await page.waitForTimeout(400);
      const a = b.assert;
      if (a.count !== undefined) ok = (await page.locator(a.selector).count()) === a.count;
      else if (a.text) ok = ((await page.evaluate(() => document.body.innerText)) || "").toLowerCase().includes(a.text.toLowerCase());
      else if (a.visible) ok = await page.locator(a.visible).first().isVisible();
      ok = ok && errors.length === 0;
    } catch (e) { note = String(e).slice(0, 160); }
    res[b.id] = { holds: ok, note };
    await context.close();
  }
  return res;
}

// ------------------------------------------------------------------ review: planted faults found, decoys left alone

function review(itemDir, outDir, spec) {
  const f = path.join(outDir, spec.report || "review.md");
  const text = fs.existsSync(f) ? fs.readFileSync(f, "utf8") : "";
  const files = [...new Set([...(spec.findings || []), ...(spec.decoys || [])].map((x) => x.file))];
  const cites = [];          // [file, from, to] for every place the review points at
  for (const line of text.split(/\n/)) {
    const named = files.filter((fn) => line.includes(fn));
    const scope = named.length ? named : (files.length === 1 ? files : []);
    const re = /(?:\.(?:css|js|html|jsx|tsx|ts)\s*[:#]\s*L?|\bL|\blines?\s+|line:\s*|第\s*)(\d+)(?:\s*[-–]\s*L?(\d+))?/gi;
    let m;
    while ((m = re.exec(line))) for (const fn of scope) cites.push([fn, +m[1], +(m[2] || m[1])]);
  }
  // each place the review points at counts for the nearest marked line (exact first), within one line
  const targets = [...(spec.findings || []).map((x) => ({ ...x, kind: "f" })), ...(spec.decoys || []).map((x) => ({ ...x, kind: "d" }))];
  const hits = new Set();
  for (const [fn, a, b] of cites) {
    const dist = (t) => (t.line < a ? a - t.line : t.line > b ? t.line - b : 0);
    const near = targets.filter((t) => t.file === fn && dist(t) <= 1).sort((x, y) => dist(x) - dist(y));
    if (near.length) for (const t of near.filter((t) => dist(t) === dist(near[0]))) hits.add(t.kind + t.id);
  }
  const found = Object.fromEntries((spec.findings || []).map((x) => [x.id, hits.has("f" + x.id)]));
  const flagged = Object.fromEntries((spec.decoys || []).map((x) => [x.id, hits.has("d" + x.id)]));
  const untouched = (spec.readonly || []).every((fn) => {
    const out = path.join(outDir, fn), orig = path.join(itemDir, fn);
    return !fs.existsSync(out) || fs.readFileSync(out).equals(fs.readFileSync(orig));
  });
  return { wrote_report: text.trim().length > 0, found, decoys_flagged: flagged, sources_untouched: untouched };
}

// ------------------------------------------------------------------ reference: the screenshot rebuilt

async function reference(browser, url, outDir, spec) {
  const { context, page } = await openPage(browser, url, { width: spec.width || 1280 });
  const vw = spec.width || 1280, vh = 900, diag = Math.hypot(vw, vh);
  const boxes = await page.evaluate((texts) => texts.map((t) => {
    const all = [...document.body.querySelectorAll("*")].filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.includes(t)));
    const el = all[0];
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }), spec.boxes.map((b) => b.text));
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  await context.close();
  const found = boxes.filter(Boolean).length / spec.boxes.length;
  const near = spec.boxes.map((b, i) => (boxes[i] ? Math.max(0, 1 - Math.hypot(boxes[i].x - (b.x + b.w / 2), boxes[i].y - (b.y + b.h / 2)) / (0.25 * diag)) : 0));
  const pos = near.reduce((a, b) => a + b, 0) / near.length;
  const rgb = (s) => (s.match(/\d+/g) || [0, 0, 0]).slice(0, 3).map(Number);
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const bgDist = Math.hypot(...rgb(bg).map((v, i) => v - hex(spec.bg)[i])) / 441;
  const html = fs.readFileSync(path.join(outDir, spec.page || "index.html"), "utf8");
  const usesImage = new RegExp(spec.png.replace(".", "\\."), "i").test(html);
  return { text_found: found, position: Math.round(pos * 100) / 100, bg_distance: Math.round(bgDist * 100) / 100,
           not_an_image: !usesImage, holds: found >= (spec.min_text || 0.9) && pos >= (spec.min_position || 0.7) && bgDist <= 0.15 && !usesImage };
}

// ------------------------------------------------------------------

async function main() {
  const [itemDir, outDir, work] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(path.join(itemDir, "_bench", "item.json"), "utf8"));
  fs.mkdirSync(work, { recursive: true });
  const out = { type: spec.type };
  if (spec.type === "review") {
    out.review = review(itemDir, outDir, spec);
    console.log(JSON.stringify(out));
    return;
  }
  const pagePath = path.join(outDir, spec.page || "index.html");
  if (!fs.existsSync(pagePath)) { out.missing = true; console.log(JSON.stringify(out)); return; }
  const url = "file://" + path.resolve(pagePath);
  const browser = await chromium.launch();
  try {
    out.layer1 = await layer1(browser, url, work);
    out.brief = await brief(browser, url, spec.must);
    if (spec.fixtures) out.fixtures = await fixtures(browser, path.resolve(outDir), path.resolve(itemDir), spec.page || "index.html", spec.fixtures);
    if (spec.interactions) out.motion = await motion(browser, url, spec.interactions);
    if (spec.behaviour) out.behaviour = await behaviour(browser, url, spec.behaviour);
    if (spec.reference) out.reference = await reference(browser, url, outDir, spec.reference);
  } finally {
    await browser.close();
  }
  out.shots = fs.readdirSync(work).filter((f) => f.endsWith(".png"));
  console.log(JSON.stringify(out));
}

main().catch((e) => { console.error(e); process.exit(1); });
