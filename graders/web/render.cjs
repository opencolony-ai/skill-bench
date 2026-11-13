#!/usr/bin/env node
// Layer 1 of the front-end exam: does the page break? Renders one page Claude wrote in headless
// Chromium, offline, and measures what a program can measure without taste. Run by CI and the judging
// schedule on the grader's machine, never inside a verifier's run.
//
//   node render.cjs <page.html> <out-dir>      writes <out-dir>/metrics.json and screenshots
//
// Every number has a plain meaning, so a person can check it against the screenshots.
"use strict";
const fs = require("fs");
const path = require("path");
let chromium;
try { ({ chromium } = require("playwright")); } catch (e) { ({ chromium } = require("@playwright/test")); }
const AXE = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

const WIDTHS = [320, 768, 1280];

async function measure(page, width) {
  return page.evaluate((width) => {
    // hidden on purpose: inside a box of 2 px or less that clips (the usual "visually hidden" text for
    // screen readers), which people never see
    const hiddenBox = (el) => {
      for (let a = el; a && a !== document.body; a = a.parentElement) {
        const s = getComputedStyle(a), r = a.getBoundingClientRect();
        if ((r.width <= 2 || r.height <= 2) && (/hidden|clip/.test(s.overflow + s.overflowX + s.overflowY) || s.clip !== "auto" || s.clipPath !== "none")) return true;
      }
      return false;
    };
    const vis = (el) => {
      const s = getComputedStyle(el), r = el.getBoundingClientRect();
      return s.visibility !== "hidden" && s.display !== "none" && +s.opacity > 0.05 && r.width > 0 && r.height > 0 && !hiddenBox(el);
    };
    const all = [...document.body.querySelectorAll("*")].filter(vis);
    const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1);
    const texts = all.filter(ownText).slice(0, 600);
    const doc = document.scrollingElement || document.documentElement;
    // elements that stick out past the right edge of the screen (the page scrolls sideways)
    const pastEdge = all.filter((el) => {
      const r = el.getBoundingClientRect();
      return r.right > width + 2 && getComputedStyle(el).position !== "fixed";
    }).length;
    // text cut off inside its box
    const clipped = texts.filter((el) => {
      const s = getComputedStyle(el);
      const hides = /hidden|clip/.test(s.overflowX + s.overflowY);
      return hides && (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2) && s.textOverflow !== "ellipsis";
    }).length;
    // two pieces of text drawn on top of each other: compared line box by line box, because an inline
    // element that wraps has one bounding box spanning both lines
    let overlaps = 0;
    const boxes = texts.map((el) => [el, [...el.getClientRects()].filter((r) => r.width > 1 && r.height > 1)]);
    const hit = (ra, rb) => {
      const w = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const h = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      return w > 4 && h > 4 && w * h > 0.2 * Math.min(ra.width * ra.height, rb.width * rb.height);
    };
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const [a, ras] = boxes[i], [b, rbs] = boxes[j];
      if (a.contains(b) || b.contains(a)) continue;
      if (ras.some((ra) => rbs.some((rb) => hit(ra, rb)))) overlaps++;
    }
    // controls too small to hit with a finger (WCAG 2.2 target size: 24 × 24 CSS px)
    const controls = all.filter((el) => el.matches("a[href],button,input:not([type=hidden]),select,textarea,[role=button],[tabindex]:not([tabindex='-1'])"));
    const smallTargets = controls.filter((el) => {
      const r = el.getBoundingClientRect();
      const inline = getComputedStyle(el).display === "inline" && el.closest("p,li,td");
      return !inline && (r.width < 24 || r.height < 24);
    }).length;
    const tinyText = texts.filter((el) => parseFloat(getComputedStyle(el).fontSize) < 12).length;
    // line length of running text, in characters per line
    const lengths = [];
    for (const p of all.filter((el) => el.matches("p,li") && el.textContent.trim().length > 120).slice(0, 40)) {
      const rg = document.createRange(); rg.selectNodeContents(p);
      const lines = new Set([...rg.getClientRects()].map((r) => Math.round(r.top))).size || 1;
      lengths.push(p.textContent.trim().length / lines);
    }
    lengths.sort((a, b) => a - b);
    return {
      width, scrollWidth: doc.scrollWidth, sideScroll: doc.scrollWidth > width + 2, pastEdge, clipped, overlaps,
      controls: controls.length, smallTargets, tinyText, textElements: texts.length,
      lineLengthMedian: lengths.length ? Math.round(lengths[Math.floor(lengths.length / 2)]) : null,
      pageHeight: doc.scrollHeight,
    };
  }, width);
}

async function axe(page) {
  await page.addScriptTag({ content: AXE });
  const r = await page.evaluate(async () => {
    const res = await window.axe.run(document, { resultTypes: ["violations"] });
    return res.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help }));
  });
  const by = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of r) by[v.impact] = (by[v.impact] || 0) + v.nodes;
  return { byImpact: by, rules: r };
}

// Tab through the page; a focus indicator counts as visible when the focused control looks different
async function focusVisible(page, limit = 12) {
  const n = await page.evaluate(() => document.querySelectorAll("a[href],button,input:not([type=hidden]),select,textarea,[tabindex]:not([tabindex='-1'])").length);
  let seen = 0, visible = 0;
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  for (let i = 0; i < Math.min(n, limit); i++) {
    await page.keyboard.press("Tab");
    const box = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      el.scrollIntoView({ block: "center", behavior: "instant" });   // pages with smooth scrolling would still be moving
      const r = el.getBoundingClientRect();
      return { x: Math.max(0, r.left - 6), y: Math.max(0, r.top - 6), width: r.width + 12, height: r.height + 12 };
    });
    if (!box || box.width < 2 || box.height < 2) continue;
    await page.waitForTimeout(50);
    const vp = page.viewportSize();
    const clip = { x: Math.min(box.x, vp.width - 2), y: Math.min(box.y, vp.height - 2) };
    clip.width = Math.max(1, Math.min(box.width, vp.width - clip.x));
    clip.height = Math.max(1, Math.min(box.height, vp.height - clip.y));
    const focused = await page.screenshot({ clip });
    await page.evaluate(() => { window.__f = document.activeElement; document.activeElement.blur(); });
    const plain = await page.screenshot({ clip });
    await page.evaluate(() => window.__f && window.__f.focus());
    seen++;
    if (!focused.equals(plain)) visible++;
  }
  return { tabbed: seen, visible };
}

async function main() {
  const [file, out] = process.argv.slice(2);
  if (!file || !out) { console.error("usage: node render.cjs <page.html> <out-dir>"); process.exit(2); }
  fs.mkdirSync(out, { recursive: true });
  const url = "file://" + path.resolve(file);
  const browser = await chromium.launch();
  const result = { file: path.basename(file), widths: {}, external: [], consoleErrors: [], pageErrors: [] };
  try {
    for (const width of WIDTHS) {
      const context = await browser.newContext({ viewport: { width, height: width < 700 ? 740 : 900 }, deviceScaleFactor: 1 });
      await context.route("**/*", (r) => {          // offline: the page must carry what it needs
        const u = r.request().url();
        if (u.startsWith("file:") || u.startsWith("data:") || u.startsWith("blob:")) return r.continue();
        if (!result.external.includes(u)) result.external.push(u);
        return r.abort();
      });
      const page = await context.newPage();
      if (width === 1280) {
        page.on("console", (m) => { if (m.type() === "error") result.consoleErrors.push(m.text().slice(0, 200)); });
        page.on("pageerror", (e) => result.pageErrors.push(String(e).slice(0, 200)));
      }
      await page.goto(url, { waitUntil: "load", timeout: 30000 });
      await page.waitForTimeout(1200);              // let entrance animations settle
      const m = await measure(page, width);
      const errorsSoFar = [result.consoleErrors.length, result.pageErrors.length];
      m.axe = await axe(page);
      if (width === 1280) {     // axe-core's own requests are not the page's errors
        result.consoleErrors.length = errorsSoFar[0];
        result.pageErrors.length = errorsSoFar[1];
      }
      await page.screenshot({ path: path.join(out, `full-${width}.png`), fullPage: true });
      if (width === 1280) {
        await page.screenshot({ path: path.join(out, "first-screen-1280.png") });
        m.focus = await focusVisible(page);
      }
      if (width === 320) await page.screenshot({ path: path.join(out, "first-screen-320.png") });
      result.widths[width] = m;
      await context.close();
    }
    // with "reduce motion" on, nothing should keep moving for long
    const rc = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: "reduce" });
    await rc.route("**/*", (r) => (/^(file|data|blob):/.test(r.request().url()) ? r.continue() : r.abort()));
    const rp = await rc.newPage();
    await rp.goto(url, { waitUntil: "load" });
    await rp.waitForTimeout(600);
    result.reducedMotion = await rp.evaluate(() => {
      const a = document.getAnimations().filter((x) => x.playState === "running");
      const long = a.filter((x) => { const t = x.effect && x.effect.getComputedTiming(); return t && (t.iterations === Infinity || t.activeDuration > 1000); });
      return { running: a.length, longOrEndless: long.length };
    });
    await rc.close();
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(out, "metrics.json"), JSON.stringify(result, null, 1));
  console.log(JSON.stringify(summary(result)));
}

function summary(r) {
  const w = r.widths;
  return {
    sideScroll320: w[320] && w[320].sideScroll, overlaps: Math.max(...Object.values(w).map((x) => x.overlaps)),
    clipped: Math.max(...Object.values(w).map((x) => x.clipped)), smallTargets320: w[320] && w[320].smallTargets,
    axeSerious: Object.values(w).reduce((n, x) => Math.max(n, x.axe.byImpact.critical + x.axe.byImpact.serious), 0),
    focusVisible: w[1280] && w[1280].focus, reducedMotion: r.reducedMotion, external: r.external.length,
    errors: r.consoleErrors.length + r.pageErrors.length,
  };
}

module.exports = { measure, axe, focusVisible, summary, WIDTHS };
if (require.main === module) main().catch((e) => { console.error(e); process.exit(1); });
