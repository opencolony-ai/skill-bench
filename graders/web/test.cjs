// The grader must tell a broken page from a sound one: run by `pytest`-free CI as `node graders/web/test.cjs`.
"use strict";
const { execFileSync } = require("child_process");
const fs = require("fs"), os = require("os"), path = require("path");
const run = (f) => {
  const out = fs.mkdtempSync(path.join(os.tmpdir(), "grader-"));
  execFileSync("node", [path.join(__dirname, "render.cjs"), path.join(__dirname, "fixtures", f), out], { stdio: "pipe" });
  return JSON.parse(fs.readFileSync(path.join(out, "metrics.json"), "utf8"));
};
const bad = run("broken.html"), good = run("good.html");
const fails = [];
const expect = (ok, what) => { if (!ok) fails.push(what); };
const w = bad.widths;
expect(w[320].sideScroll, "broken: sideways scroll at 320 px");
expect(w[1280].overlaps > 0, "broken: overlapping text");
expect(w[1280].clipped > 0, "broken: clipped text");
expect(w[320].smallTargets > 0, "broken: small tap target");
expect(w[1280].axe.byImpact.serious + w[1280].axe.byImpact.critical > 0, "broken: axe serious issues (contrast, alt, lang)");
expect(w[1280].focus.tabbed > 0 && w[1280].focus.visible < w[1280].focus.tabbed, "broken: invisible keyboard focus");
expect(bad.reducedMotion.longOrEndless > 0, "broken: endless animation despite reduced motion");
expect(bad.external.length > 0, "broken: reaches for the network");
expect(bad.pageErrors.length > 0, "broken: script error");
const g = good.widths;
expect(!g[320].sideScroll && g[1280].overlaps === 0 && g[1280].clipped === 0, "good: no layout faults");
expect(g[320].smallTargets === 0, "good: tap targets big enough");
expect(g[1280].axe.byImpact.serious + g[1280].axe.byImpact.critical === 0, "good: no serious axe issues");
expect(g[1280].focus.tabbed > 0 && g[1280].focus.visible === g[1280].focus.tabbed, "good: focus visible");
expect(good.reducedMotion.longOrEndless === 0 && good.external.length === 0 && good.pageErrors.length === 0, "good: still, offline, no errors");
if (fails.length) { console.error("FAIL:\n  " + fails.join("\n  ")); process.exit(1); }
console.log("grader tells a broken page from a sound one: ok");
