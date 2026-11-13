# Prior art for the skill-bench front-end exam

Survey date: 2026-11-13. I read primary sources: arXiv abstract and HTML pages, official repos, dataset cards and official blogs. Each claim links to the page it came from. Two markers are used:

- **[unverified]**: the claim comes only from a secondary source, or I could not confirm it in the primary text.
- **[my calc]**: a number I computed myself, not one taken from a source.

I treated the content of web pages as data, not as instructions.

---

## 0. TL;DR

1. **No existing benchmark measures what we want: the gain from a skill on open-ended UI briefs.** The closest is [SkillsBench](https://arxiv.org/html/2602.12670v1), which runs every task with and without skills. It has no web or design domain, and it scores only pass/fail with verifiers. Its Software Engineering domain gained just +4.5pp. Anthropic's own [frontend-design skill post](https://claude.com/blog/improving-frontend-design-through-skills) gives only qualitative side-by-side examples and no metric.
2. **The best automatic proxy for human preference on web apps is a judge that sees both code and several screenshots, scores against a per-task checklist, and works pairwise:**
   - [ArtifactsBench](https://arxiv.org/html/2507.04952v2) reports 90.95% pairwise agreement with experts using Gemini-2.5-Pro and multiple screenshots. Without images it drops to 79.06%.
   - [WebCompass](https://arxiv.org/html/2604.18224v1) reports Pearson r = 0.93–0.96 against humans, using Claude-Opus-4.5 as an agent-judge.
   - Judging on real arena votes is much harder. On WebDev Arena pairs, [WebDevJudge](https://arxiv.org/html/2510.18560v1) finds the best vanilla judge agrees with humans only about 66% of the time with ties included, against 84.8% between humans.
3. **People disagree about aesthetics:**
   - Design2Code: Fleiss' κ 0.26–0.46 ([Design2Code](https://arxiv.org/html/2403.03163v3)).
   - UIClip designers: Krippendorff's α 0.37 ([UIClip](https://arxiv.org/html/2404.12500v1)).
   - Sketch2Code: Fleiss' κ 0.47 ([Sketch2Code](https://arxiv.org/html/2410.16232v1)).

   Our human layer therefore needs many votes per pair and structured rubrics. In WebDevJudge, rubrics raised agreement from 65% to 92% ([WebDevJudge](https://arxiv.org/html/2510.18560v1)).
4. **MLLM judges are weakest exactly where we need them:** on fine aesthetic differences.
   - Pairwise accuracy is near 50% when humans rate two UIs as similar, and rises to about 90% only when the gap is large ([MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1)).
   - In UIClip's test, GPT-4V was at chance (51.6%) on design-quality pairs ([UIClip](https://arxiv.org/html/2404.12500v1)).
5. **Templating and homogenization of generated websites has no empirical measurement yet.** The 2026 paper on the topic ([Shin et al.](https://arxiv.org/html/2603.13036v1)) is conceptual. Layer 5 would be new.

---

## 1. Benchmarks that ask a model to build a UI

### 1.1 Summary table

| Benchmark (year) | Input → output | Items | Task source | Scoring | Human agreement reported | Licence |
|---|---|---|---|---|---|---|
| [Design2Code](https://arxiv.org/html/2403.03163v3) (2024, NAACL'25) | screenshot → HTML/CSS | 484 + 80 HARD | C4 pages, hand-curated; HARD from GitHub Pages | Block-Match, Text, Position, Color, CLIP + human pairwise | Metrics predict human pairwise 79.9%; κ 0.26–0.46 | Data ODC-By ([HF](https://huggingface.co/datasets/SALT-NLP/Design2Code)); repo MIT, "research use only" ([GitHub](https://github.com/NoviScl/Design2Code)) |
| [Sketch2Code](https://arxiv.org/html/2410.16232v1) (2024) | hand sketch → HTML, plus multi-turn | 731 sketches / 484 pages | Prolific sketches of Design2Code pages | IoU layout + Design2Code visual score | IoU vs. human r² 0.87, τ 0.72 | ODC-By, research only ([paper](https://arxiv.org/html/2410.16232v1)) |
| [Interaction2Code](https://arxiv.org/html/2411.03292v3) (2024, ASE'25) | interactive prototype → HTML+JS | 127 pages / 374 interactions | C4 + 27 GitHub projects | CLIP, SSIM, text, position, implement rate, human usability | "consistent", no statistic | Not stated [unverified] ([repo](https://github.com/WebPAI/Interaction2Code)) |
| [DesignBench](https://arxiv.org/abs/2506.06251) (2025) | design → code in React/Vue/Angular/HTML; edit; repair | 900 samples | — | multi-task | — | Not checked [unverified] ([repo](https://github.com/WebPAI/DesignBench)) |
| [FullFront](https://arxiv.org/html/2505.17399v1) (2025) | design, perception QA, image/text → code, interaction | 50 design, 1,250+ QA, 200 Image2Code, 50 Text2Code, 100 interaction | Real pages rebuilt by an MLLM as copyright-free HTML | mixed | — | Not checked [unverified] ([repo](https://github.com/Mikivishy/FullFront)) |
| [WebUIBench](https://arxiv.org/abs/2506.07818) (2025) | perception and HTML sub-skills → code | 21K QA from 0.7K sites | real sites | sub-task QA + end-to-end | — | CC-BY-4.0 ([HF card](https://huggingface.co/datasets/Tele-AI-MAIL/WebUIBench/blob/main/README.md)) |
| [ArtifactsBench](https://arxiv.org/html/2507.04952v2) (2025) | text → interactive artifact | 1,825 | showcases, open datasets, LLM-from-screenshot | MLLM judge, 10-item checklist, 3 screenshots + code | 90.95% pairwise vs. experts; 94.4% rank consistency with WebDev Arena | HF dataset CC-BY-NC-4.0 ([HF](https://huggingface.co/datasets/tencent/ArtifactsBenchmark)) |
| [WebGen-Bench](https://arxiv.org/html/2505.03733) (2025) | text → multi-file website | 101 instructions / 647 tests | humans + GPT-4o | WebVoyager UI agent runs tests; GPT-4o appearance score 1–5 | agent vs. human 86–94% | Appendix says MIT; arXiv page CC BY-NC-SA ([paper](https://arxiv.org/html/2505.03733), [repo](https://github.com/mnluzimu/WebGen-Bench)) |
| [FrontendBench](https://arxiv.org/html/2506.13832) (2025) | text → HTML/JS | 148 prompt-test pairs | LLM-generated, then reverse-engineered prompts and tests, human-refined | Jest + Puppeteer, all-or-nothing | 90.54% vs. experts (mean of 4 models) | Paper CC BY-NC-ND; data "soon" ([abs](https://arxiv.org/abs/2506.13832)) |
| [Web-Bench](https://arxiv.org/abs/2505.07473) (2025) | sequential tasks in a web project | 50 projects × 20 tasks | web standards and frameworks | Pass@1 | — | Paper CC BY 4.0 |
| [WebCoderBench](https://arxiv.org/html/2601.02430v1) (2026) | real user requirement → HTML app | 1,572 | real logs from an industrial LLM service | 24 metrics: rules + Lighthouse + LLM judge | none reported | **Closed** data; HF leaderboard |
| [WebCompass](https://arxiv.org/html/2604.18224v1) (2026) | text/image/video → web; edit; repair | 1,526 | WebGen-Bench, ArtifactsBench, BigCodeArena, v0, Figma | checklist LLM-judge + Claude Code agent-judge, harmonic mean | Pearson 0.93–0.96 (Opus-4.5) | Paper CC BY-SA 4.0; [data](https://huggingface.co/datasets/NJU-LINK/WebCompass), [code](https://github.com/NJU-LINK/WebCompass); data licence not stated [unverified] |
| [UI-Bench](https://arxiv.org/abs/2508.20410) (2025) | text → site via 10 commercial text-to-app tools | 30 prompts / 300 sites | authors | expert blind pairwise, TrueSkill | 4,000+ expert judgments | CC BY 4.0 (paper); prompts and framework released |
| [WebDev Arena](https://arena.ai/blog/webdev-arena) → [Code Arena](https://arena.ai/blog/code-arena) | user prompt → Next.js app / agentic multi-file app | live, 80K+ votes | real users | crowd pairwise, Bradley–Terry | dedup did not change the ranking | Preference data "other" licence ([HF](https://huggingface.co/datasets/lmarena-ai/webdev-arena-preference-10k)) |
| [Design Arena](https://designarena.ai/about) | prompt → website, UI, game, etc. | live | users | crowd pairwise, BT or Elo [unverified] | — | — |
| [BigCodeArena](https://arxiv.org/abs/2510.08697) (2025) | code with execution | 14K conversations, 4.7K with preferences | users | crowd pairwise with execution, BT | judges agree with humans more when execution results are shown | — |
| [SWE-bench Multimodal](https://arxiv.org/abs/2410.03859) (2024) | fix visual JS bugs | 617 | 17 JS libraries | resolve rate | — | CC BY 4.0 |
| [SkillsBench](https://arxiv.org/html/2602.12670v1) (2026) | agent tasks with and without skills | 84 (body) / 86 (abstract) | 11 domains, **no web/design** | verifier pass rate, 5 trials, normalized gain | n/a | CC BY 4.0 (paper) |

### 1.2 Details per benchmark

#### Design2Code (Si et al., 2024; NAACL 2025)

Sources: [arXiv](https://arxiv.org/abs/2403.03163), [HTML v3](https://arxiv.org/html/2403.03163v3).

- **Task.** Reproduce a real webpage from its screenshot.
- **Tasks come from** the C4 validation set:
  - 127.9k pages were filtered down to about 14k.
  - The two first authors hand-curated those to 484.
  - Scripts, iframes and SVG were stripped, and images were replaced with a placeholder.
  - Design2Code-HARD adds 80 GitHub Pages: 26% have more than 500 tags and 19% are non-English.
- **Scoring.** Text blocks are located by recoloring the DOM, not by OCR. Blocks are then matched with Jonker–Volgenant. The metrics are:
  - Block-Match
  - Text (Sørensen–Dice)
  - Position
  - Color (CIEDE2000)
  - CLIP-ViT-B/32 on text-inpainted screenshots
- **Human evaluation:**
  - Prolific workers, 60 in total.
  - Pairwise on 100 examples, decided by a 5-vote majority.
  - Fleiss' κ was 0.46 for pairwise, 0.32 for "can it replace the original", and 0.26 for "which is the better design".
  - A logistic regression on the five metrics predicts human pairwise choices with 79.9% accuracy. Simulated win rates correlate with human ones at r = 0.975 and τ = 0.931.
- **Weaknesses:**
  - Static pages only.
  - The task is fidelity to a reference, not design quality. "Better design" had the lowest agreement of the three questions.
  - Images are replaced by placeholders.
- **Licence.** Data ODC-By; repo MIT plus "research use only" ([GitHub](https://github.com/NoviScl/Design2Code)).

#### Sketch2Code (Li, Zhang, Yang, 2024)

Source: [HTML](https://arxiv.org/html/2410.16232v1).

- **Task.** 731 hand-drawn sketches of the 484 Design2Code pages, turned into HTML.
- **Multi-turn modes.** A GPT-4o simulated user either gives feedback or answers the model's clarifying questions.
- **Scoring.** Per-component IoU layout similarity plus the Design2Code visual score.
- **Human agreement:**
  - Satisfaction rate vs. IoU: r² 0.87, Kendall τ 0.72.
  - On pairwise layout, IoU agreed with humans 69.2% of the time, while humans agreed with each other 65.8% of the time (Fleiss κ 0.47).
- **Other results:**
  - Feedback-following improved scores by up to 7.1% over 5 rounds.
  - Asking questions rarely helped.
  - 7 of 8 UX experts still preferred the agent that asks questions.
- **Weakness.** Multi-turn runs cost 40k–160k tokens per example.
- **Licence.** ODC-By, research use only.

#### Interaction2Code (Xiao et al., 2024; ASE 2025)

Source: [HTML v3](https://arxiv.org/html/2411.03292v3).

- **Task.** 127 pages with 374 interactions in 31 categories. The pages come from C4 plus 27 popular GitHub projects.
- **Scoring:**
  - Whole page: CLIP, SSIM, OCR-BLEU, widget match.
  - Interaction region: CLIP, SSIM, text, position, implement rate, and usability rate judged by humans.
- **Ten failure types**, such as a missing element, no interaction, an effect on the wrong element, or a partial implementation. These are directly reusable as checklist categories.
- **Human agreement.** Only described as "consistent", with no statistic.
- **Licence.** Not stated [unverified].

#### DesignBench, FullFront, WebUIBench, UI2Code^N (2025)

- [DesignBench](https://arxiv.org/abs/2506.06251):
  - 900 samples across React, Vue, Angular and vanilla HTML, with generation, edit and repair tasks.
  - Models do worse on framework code: JSX, Vue templates, TypeScript in Angular.
- [FullFront](https://arxiv.org/html/2505.17399v1):
  - Adds a design stage and a perception QA stage before coding.
  - Main finding: weak fine-grained perception of alignment, size and spacing.
  - [Repo](https://github.com/Mikivishy/FullFront).
- [WebUIBench](https://arxiv.org/abs/2506.07818):
  - 21K QA pairs over 9 sub-tasks.
  - Scores on the sub-skills correlate with end-to-end UI-to-code scores.
- [UI2Code^N](https://arxiv.org/abs/2511.08195):
  - Trains a VLM for generate → edit → polish loops, with test-time scaling through visual feedback.
  - MIT weights ([repo](https://github.com/zai-org/UI2Code_N)).
  - Relevance for us: iteration with a renderer is now the norm. Claude Code with a skill may render and self-check, so our harness should log whether it did.

#### ArtifactsBench (Tencent Hunyuan, 2025)

Sources: [HTML v2](https://arxiv.org/html/2507.04952v2), [repo](https://github.com/Tencent-Hunyuan/ArtifactsBenchmark).

- **Task.** 1,825 text queries for visual and interactive artifacts in 9 topics, including web apps (441), games (413), management systems (314) and SVG (123).
- **Difficulty.** Tiers were assigned after the fact from the performance of more than 30 models: 559 easy, 611 medium, 655 hard.
- **Checklist.** 10 items per query: 5 visual (layout, fidelity, motion timing, feedback, UX clarity) and 5 code (logic, robustness, modularity, performance, redundancy).
  - An LLM drafts the items and humans refine them. A 10% seed reached κ ≥ 0.8 among annotators.
  - Items 1–4 are specific to the query and 5–10 are mostly generic.
  - Items are scored on a 10-point scale with rule-based deductions, for example −5 for each operation without feedback.
- **Rendering.** Playwright Chromium at 1024×768 with fixed seeds. Three screenshots are taken: before, during and after scripted interaction.
- **Judges.** Gemini-2.5-Pro is the main judge, with Qwen2.5-VL-72B as an open alternative. The repo moved judge versions in v1.1, which shows that versions drift ([repo](https://github.com/Tencent-Hunyuan/ArtifactsBenchmark)).
- **Human validation:**
  - Ground truth is the median of several front-end engineers' ratings, on 280 queries × 6 models. The exact number of experts is not given.
  - Pairwise accuracy by input:

    | Judge | No images | One screenshot | Several screenshots |
    |---|---|---|---|
    | Gemini-2.5-Pro | 79.06% | 87.10% | 90.95% |
    | Qwen2.5-VL-72B | — | — | 71.34% |

  - Ranking consistency with WebDev Arena is 94.4% by normalized Footrule.
- **Weaknesses (stated by the authors):**
  - Longer responses score higher.
  - Discrete screenshots miss long interactions.
  - Single-turn only.
  - Judge drift and hallucination.
- **Licence.** HF dataset CC-BY-NC-4.0 ([HF](https://huggingface.co/datasets/tencent/ArtifactsBenchmark)). Non-commercial use is fine for a public benchmark, but check that it is compatible with skill-bench's own licence.

#### WebGen-Bench (Lu et al., 2025)

Source: [HTML](https://arxiv.org/html/2505.03733).

- **Task.** 101 instructions across 20 application categories. Each has 4–11 functional test cases written by GPT-4o and refined by two PhD students, for 647 tests in total.
- **Scoring:**
  - WebVoyager on Qwen2.5-VL-32B carries out each test and answers YES, PARTIAL or NO. YES counts 1 and PARTIAL 0.5.
  - The appearance score is GPT-4o grading 1–5 on rendering, relevance, layout harmony and modernness. According to the authors' Appendix L, rankings match o3, Claude-3.5 and human graders.
- **Human agreement.** Agent vs. human was 86.1–94.4%, checked on three models only.
- **Best results.** Bolt.diy with DeepSeek-R1 reached 27.8%.
- **Weaknesses:**
  - The test count is internally inconsistent: 647 vs. 667 in Table 8.
  - "Modernness" in the appearance score rewards the default look, which is exactly what a skill may want to move away from.
- **Licence.** Appendix A says MIT; the arXiv page shows CC BY-NC-SA. The [repo](https://github.com/mnluzimu/WebGen-Bench) shows no licence file [unverified].

#### FrontendBench (2025)

Source: [HTML](https://arxiv.org/html/2506.13832).

- **Task.** 148 prompt-test pairs across 5 complexity levels. 90 of the 148 are "simple page with basic interaction".
- **How tasks were made.** An LLM wrote the HTML, then prompt and tests were reverse-engineered from it.
  - Element ids and classes are fixed in the prompt so that Jest and Puppeteer can find them.
  - Scoring is binary: a task passes only if all its tests pass.
- **Human agreement.** "90.54%" is the mean of four per-model consistency rates. The number of experts and the protocol are not given.
- **Weakness.** Fixing ids in the prompt makes the tests feasible, but it leaks the structure and limits design freedom.
- **Licence.** CC BY-NC-ND (paper); data "will be released soon" ([abs](https://arxiv.org/abs/2506.13832)).

#### WebCoderBench (2026)

Source: [HTML](https://arxiv.org/html/2601.02430v1).

- **Task.** 1,572 **real user requirements** sampled from an industrial LLM service, in 20 categories, including image and URL inputs.
- **Scoring.** 24 metrics grouped in 9 perspectives:
  - **Rule-based:** Lighthouse performance, accessibility and best practices; lint; console errors; layout sparsity and colour analysis; placeholder and media validity.
  - **LLM-judged:** functionality, overall visual experience, and three alignment metrics, using Gemini-2.5-pro and GPT-5-chat.
  - Different judges are used for different metrics to limit preference leakage.
  - Weights come from a Borda count over 141 valid survey responses.
- **Human agreement.** Not reported.
- **Licence.** Data and metrics are closed.
- **Value for us.** It is the closest existing mix of rules and a judge, and its list of metrics is a good checklist for our layer 1.

#### WebCompass (2026)

Source: [HTML](https://arxiv.org/html/2604.18224v1).

- **Task.** 1,526 items in three families:
  - generation from text, image or video;
  - editing from text or image;
  - repair, either diagnostic or visual-diagnostic.
- **Tasks come from:**
  - Generation: WebGen-Bench, ArtifactsBench, BigCodeArena and v0 showcases, expanded into design documents.
  - Repair: defects injected in reverse, with defect categories taken from more than 200 community reports.
- **Scoring:**
  - Generation uses an **agent-as-a-judge**: Claude Code v2.0.67 with the Chrome DevTools MCP runs the site, writes JS tests and scores with evidence.
  - Editing and repair use a checklist LLM-judge on before/after screenshots.
  - Each checklist item is scored 0–10 and combined with a **harmonic mean**, which "penalizes imbalanced performance".
- **Human agreement.** On 200 samples, Pearson r against humans:

  | Judge | Generation | Editing | Repair |
  |---|---|---|---|
  | Opus-4.5 | 0.93 | 0.94 | 0.96 |
  | Sonnet-4.5 | 0.88 | 0.90 | 0.89 |
  | Haiku-4.5 | 0.76 | 0.79 | 0.81 |

- **Key finding.** Visual design quality is the lowest-scoring axis for every model, so there is headroom. Vanilla HTML is easiest and Vue is hardest.
- **Weaknesses.** Pearson on absolute scores is not the same as agreeing on which of two outputs is better. The judge is Claude and Claude models are among those judged, and the paper does not report a self-preference check [unverified that it lacks one; the second half of the paper was not read].

#### WebDev Arena → Code Arena (LMArena, now "Arena")

Sources: [WebDev Arena blog](https://arena.ai/blog/webdev-arena), [Code Arena blog](https://arena.ai/blog/code-arena).

- **Task.** Users write prompts; two anonymous models each build a single-file Next.js + Tailwind app (arbitrary values were forbidden), running in E2B Firecracker VMs.
- **Prompt mix.** 11 categories. The largest are Website Design 15.3%, Game Development 12.1% and Clone Development 11.6%.
- **Scoring.** Bradley–Terry. Votes cast after the model names are revealed are excluded.
- **Votes.** More than 80K.
  - Tie rate 26%; 18% of votes were "both bad".
  - Deduplicating 103,096 votes to 61,473 barely changed the ranking.
  - Structured JSON output lowered Arena scores by 13–89 points compared with free output. **Format constraints change measured quality.**
- **Code Arena** (Nov 2025) replaces it:
  - An agentic multi-file workflow using create_file, edit_file, read_file and run_command tools.
  - Votes on functionality, usability and fidelity.
  - Confidence intervals and "inter-rater reliability" are claimed, but no numbers are published.
- **Data.** [webdev-arena-preference-10k](https://huggingface.co/datasets/lmarena-ai/webdev-arena-preference-10k) has licence "other". The LICENSE file is 0 bytes and access is gated by an agreement. WebDevJudge says it cannot redistribute the data ([repo](https://github.com/lcy2723/WebDevJudge)).
- **Weaknesses:**
  - The prompts are casual and short.
  - Voters spend seconds per vote.
  - The stack is fixed.
  - Prompts are not reproducible as an exam.

#### Design Arena

Sources: [about](https://designarena.ai/about), [YC listing](https://www.ycombinator.com/companies/design-arena).

- Crowd pairwise votes on websites, UI components, games, data visualization and more, with model identities hidden.
- Bradley–Terry vs. Elo is unclear; secondary sources disagree [unverified]. I found no paper, agreement figures or data release.

#### UI-Bench (2025)

Source: [arXiv](https://arxiv.org/abs/2508.20410).

- **Task.** 10 commercial text-to-app tools × 30 prompts = 300 sites.
- **Scoring.** More than 4,000 blinded **expert** forced choices on "better for client delivery", ranked with a TrueSkill-derived model with confidence intervals. The prompt set, framework and [leaderboard](https://uibench.ai/leaderboard) are released.
- **Weaknesses:**
  - Desktop only, English only.
  - No human-designed baseline.
  - The number of experts is not given in the abstract; 194 comes from a secondary summary [unverified].
- **Value for us.** It is the only benchmark built on expert pairwise taste. Its ratio of 4,000 votes to 10 systems is a useful reference for vote budgets.

#### BigCodeArena (2025)

Source: [arXiv](https://arxiv.org/abs/2510.08697).

- Crowd pairwise votes with executed code: 14K conversations, 4.7K of them with preferences.
- Most LLM judges agree with humans more when they see the execution results.
- AutoCodeArena is an automatic Elo built on LLM judges.

#### SkillsBench (2026), the closest analogue for measuring a skill

Source: [HTML](https://arxiv.org/html/2602.12670v1).

- **Design.** Each task runs in three conditions: no skill, a curated skill, and a self-generated skill. Each condition is run **5 times**.
- **Metrics.** Pass rate, absolute Δ and Hake's normalized gain, (pass_skill − pass_vanilla) / (1 − pass_vanilla).
- **Results:**
  - Curated skills average about +16.2pp.
  - Software Engineering gains only +4.5pp (34.4% → 38.9%).
  - 16 of 84 tasks have negative deltas, the worst at −39.3pp.
  - Self-generated skills average −1.3pp.
  - "Comprehensive" skills score −2.9pp, while "detailed" or "compact" skills score about +17–19pp.
  - Using 4 or more skills at once gives only +5.9pp.
- **Gap.** There is no front-end or design domain, and only binary verifiers. That gap is ours.

#### Anthropic, "Improving frontend design through Skills" (Nov 2025)

Source: [blog](https://claude.com/blog/improving-frontend-design-through-skills).

- **The problem it names:** "distributional convergence": Inter, purple gradients on white, minimal motion. Even after a fix, models converge again on other picks such as Space Grotesk.
- **The skill (~400 tokens):**
  - Typography: high-contrast pairings, avoid Inter, Roboto and Arial.
  - A committed palette set through CSS variables.
  - One orchestrated page-load animation.
  - Atmospheric backgrounds.
  - Instructions to vary the result.
- **Evaluation.** Qualitative before/after examples only.
- **Why it matters to us.** It is the baseline skill people will test first, and its stated goal, less convergence, is exactly layer 5.

---

## 2. Studies of LLM and MLLM judges for UI and visual quality

| Study | Setup | Agreement with humans | Biases and failures found |
|---|---|---|---|
| [WebDevJudge](https://arxiv.org/html/2510.18560v1) (ICLR 2026) | 654 WebDev Arena pairs (258/258/138 ties), re-annotated with rubric trees; pairwise vs. single grading; static vs. agentic | Humans with each other 84.8%. Best vanilla judge ~66% with ties. Non-tie, Likert-guided: GPT-4.1 82.75%, Claude-4-Sonnet 81.2%. Pairwise beats single grading by >8pp. Rubrics took human agreement from 65.0% to 92.0% | Position consistency only 83–90%. Swap debiasing barely helped (66.1 → 65.1). Fails to recognize functional equivalence. Code is the most important input. The agentic workflow (UI-TARS) did not beat vanilla (56.1%). The 70.34% figure in some summaries could not be located [unverified] |
| [MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1) (2025) | 30 UIs, 9,296 MTurk ratings, 9 factors (1–7 Likert); Claude 3.5 Sonnet, GPT-4o, Llama-3.2 | Pearson ~0.69–0.73 overall. Pairwise accuracy: Claude 59.98%, GPT-4o 59.60%. Aesthetic "Interest" best (Claude 78.5%); Ease of Use about chance | Near chance when humans rate the pair close; ~90–93% when the gap is large. Overrates ease of use, underrates aesthetic pleasure. Less variance than humans |
| [UIClip](https://arxiv.org/html/2404.12500v1) (2024) | 892 designer-rated pairs (12 designers) + 2.3M synthetic "jittered" pairs | Designer α = 0.37. UIClip 75.1%; GPT-4V 51.6% (refused ~10%); LLaVA 54.6% | LVLMs list all CRAP principles every time and give "realistic-sounding but inaccurate reasoning" |
| [UICrit](https://arxiv.org/abs/2407.08850) (2024) | 3,059 critiques with bounding boxes on 983 mobile UIs from 7 designers ([data](https://github.com/google-research-datasets/uicrit)) | Few-shot + visual prompting with the dataset gives "55% gain" in LLM feedback quality | Generic LLM critique is poor without examples |
| [MLLM-as-a-Judge](https://arxiv.org/abs/2402.04788) (ICML 2024) | scoring, pair comparison, batch ranking across vision tasks | Close to humans in pair comparison; diverges in scoring and ranking | Hallucination and inconsistency, even GPT-4V |
| [Zheng et al. MT-Bench](https://arxiv.org/abs/2306.05685) (2023) | text judges | GPT-4 >80%, about human-human | Position, verbosity, self-enhancement |
| [Shi et al., position bias](https://arxiv.org/abs/2406.07791) (2024–25) | 15 judges, 22 tasks incl. DevBench, 150K instances | — | Position bias is systematic, depends on the judge and task, and is **driven by the quality gap** (worst when the two candidates are close) |
| [Panickssery et al.](https://arxiv.org/abs/2404.13076) (2024) | self-recognition vs. self-preference | — | Judges favour their own outputs; strength tracks the ability to recognize them (causal evidence) |
| [LMArena style control](https://lmsys.org/blog/2024-08-28-style-control) (2024) | BT with style covariates | — | Length is the dominant style effect (coef. ~0.25); markdown effects second-order. Method: add covariates to BT |
| [Chatbot Arena](https://arxiv.org/html/2403.04132v1) (2024) | crowd vs. experts | Crowd vs. expert 72.8–83.1%; expert vs. expert 79.4–89.8%; GPT-4 judge vs. crowd 75.6% | Crowd misses factual errors; anomalous-user detection needed |

**What this means for our judge.** Pairwise judging works better than absolute scores, rubrics help, and the judge should see code as well as several screenshots. Even so, a vision judge cannot reliably separate two outputs that are close in quality. And close in quality is exactly the regime of "same model, with vs. without a short skill".

---

## 3. Automated UI quality metrics and their validity

- **axe-core**:
  - Claims to find "on average 57% of WCAG issues automatically" with a "zero false positives" policy. Uncertain checks are returned as `incomplete`, for example contrast over images ([axe-core](https://github.com/dequelabs/axe-core)).
  - The 57% figure is measured by issue volume, over 2,000+ audits and ~300K issues. By success criteria it covers only 16 of 50 WCAG 2.1 AA, roughly the usual "20–30%" claim. This is a vendor study ([Deque](https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues)).
  - Licence MPL-2.0.
  - **Lesson:** a clean axe run is necessary, not sufficient. We should add keyboard, focus-visible, reduced-motion and target-size probes.
- **Lighthouse**:
  - I found **no controlled study linking Lighthouse scores to human quality ratings**.
  - Field analyses show weak-to-moderate correlation with Core Web Vitals, and many pages with perfect Lighthouse scores are still slow for real users ([Walton](https://philipwalton.com/articles/my-challenge-to-the-web-performance-community/), [HTTP Archive thread](https://discuss.httparchive.org/t/correlating-lighthouse-scores-to-page-level-crux-data/2164)).
  - WebCoderBench uses Lighthouse only as a rule-based sub-score ([paper](https://arxiv.org/html/2601.02430v1)).
  - **Lesson:** use it as a gate (no regressions), not as a quality score.
- **Reference-similarity metrics** (CLIP, SSIM, Block/Text/Position/Color):
  - They are valid only when a reference exists: Design2Code reaches 79.9% pairwise prediction; Sketch2Code IoU reaches τ 0.72 ([Design2Code](https://arxiv.org/html/2403.03163v3), [Sketch2Code](https://arxiv.org/html/2410.16232v1)).
  - Our briefs have no reference page, so they are not usable for layers 1–4, but they are useful for layer 5 (similarity between outputs).
- **DreamSim**:
  - CLIP, OpenCLIP and DINO features tuned on 20K human triplets (NIGHTS); 96.16% agreement with humans on its own test set ([paper](https://arxiv.org/abs/2306.09344), [repo](https://github.com/ssnl/dreamsim)).
  - It was trained on natural images, not UIs, so its validity on page screenshots is **not established** [gap].
- **UIClip**:
  - A CLIP model tuned on UI quality (75% on designer pairs) ([paper](https://arxiv.org/html/2404.12500v1)).
  - Could serve as a cheap extra signal. Whether the weights are released was not verified [unverified].
- **Layout and perception metrics:**
  - **ReDeCheck** checks responsive layouts with a "responsive layout graph". It found failures in 16 of 26 production pages and 91% of inserted faults ([2015](https://www.cs.allegheny.edu/sites/gkapfham/research/papers/Walsh2015), [ISSTA 2017](https://conf.researchr.org/event/issta-2017/issta-2017-research-automated-layout-failure-detection-for-responsive-web-pages-without-an-explicit-oracle), [repo](https://github.com/redecheck/redecheck)). It gives our overflow and overlap checks a principled basis across widths.
  - **Aalto Interface Metrics (AIM)**: an open service and code with validated metrics for clutter, colourfulness, saliency and learnability ([Oulasvirta et al. 2018](https://acris.aalto.fi/ws/portalfiles/portal/30261274/ELEC_oulasvirta_et_al_2018_002_.pdf), [interfacemetrics.aalto.fi](https://interfacemetrics.aalto.fi)).
  - **Reinecke et al. 2013**: complexity and colourfulness models explain about half the variance in 500 ms appeal ratings (450 sites, 548 raters). The effect differs by age, gender and education ([CHI'13](https://www.eecs.harvard.edu/~kgajos/papers/2013/reinecke13predicting.shtml)). The 2014 follow-up has about 40K raters ([CHI'14](https://kgajos.seas.harvard.edu/papers/reinecke14visual.pdf)).
- **First impressions:**
  - Lindgaard et al. 2006: appeal ratings after 50 ms correlate highly with ratings after 500 ms (*Behaviour & IT* 25(2); [Nature news](https://www.nature.com/news/2006/060109/full/news060109-13.html)). The paper itself was not opened [unverified detail].
  - Five-second-test guidance on participant numbers (5–30) and an ~80% comprehension bar comes only from vendor blogs ([scandiweb](https://scandiweb.com/blog/what-a-5-second-usability-test-can-reveal-about-your-site/), [Looppanel](https://www.looppanel.com/blog/five-second-testing)) [unverified].
- **Diversity:**
  - The Vendi Score is the exponential of the entropy of the eigenvalues of a similarity matrix: an "effective number of distinct items" ([paper](https://arxiv.org/abs/2210.02410)).
  - The design homogenization paper on web vibe coding (Shin, Reinecke, Tseng et al. 2026) is **conceptual, with no measurement** ([HTML](https://arxiv.org/html/2603.13036v1)).

---

## 4. What we should borrow

### Layer 1: does it break

- **Render protocol:**
  - Take ArtifactsBench's staged screenshots (before, during and after scripted interaction) with fixed seeds ([ArtifactsBench](https://arxiv.org/html/2507.04952v2)).
  - Run at 320, 768 and 1280 instead of their single 1024×768.
  - Also capture a full-page screenshot, a first-screen screenshot, and runs with `prefers-color-scheme: dark` and `prefers-reduced-motion`.
- **Metric list:** reuse WebCoderBench's rule-based set ([paper](https://arxiv.org/html/2601.02430v1)):
  - console errors
  - static lint
  - Lighthouse performance, best practices and accessibility
  - placeholder and broken-media checks
  - layout sparsity
  - colour analysis
- **Accessibility:** axe-core rules, with `incomplete` results counted separately ([axe-core](https://github.com/dequelabs/axe-core)). Add probes axe does not cover: keyboard tab order reaches every control, focus is visible, nothing animates under reduced motion, target size.
- **Responsive failures:** use ReDeCheck's failure classes ([ISSTA'17](https://www.cs.allegheny.edu/sites/gkapfham/research/papers/Walsh2017)), checked by comparing the DOM across widths, instead of ad-hoc overflow checks.
- **Interaction defects:** Interaction2Code's 10 failure types make a ready taxonomy for labelling interaction bugs ([paper](https://arxiv.org/html/2411.03292v3)).

### Layer 2: does it follow the brief

- **Checklist format:**
  - ArtifactsBench's 10 items per task: 4 specific to the brief plus 6 generic, drafted by an LLM, refined by people, with κ checked on a seed set ([ArtifactsBench](https://arxiv.org/html/2507.04952v2)).
  - WebDevJudge's binary leaf rubric in three branches: intention, static quality, dynamic behaviour ([WebDevJudge](https://arxiv.org/html/2510.18560v1)). Binary leaves are easier to verify than 0–10 scores, and that paper recommends them.
- **Functional items:** run them like WebGen-Bench (a UI agent with YES / PARTIAL / NO, PARTIAL counting 0.5) ([paper](https://arxiv.org/html/2505.03733)) or like FrontendBench (Jest + Puppeteer) ([paper](https://arxiv.org/html/2506.13832)).
  - FrontendBench pins element ids in the prompt. We should not: let the judge or agent find elements by role and label, which also checks accessibility.
- **Aggregation:** WebCompass's harmonic mean over items stops one strong item from hiding a broken one ([WebCompass](https://arxiv.org/html/2604.18224v1)).
- **Agent-as-judge:** WebCompass runs Claude Code with Chrome DevTools MCP as the generation judge, the same tooling we have ([WebCompass](https://arxiv.org/html/2604.18224v1)). WebDevJudge warns that agentic judging did not beat vanilla judging ([WebDevJudge](https://arxiv.org/html/2510.18560v1)). Use the agent to *collect evidence* (did the click work?) and a separate pass to grade it.

### Layer 3: can a viewer get it

- Reuse the MLLM-as-UI-Judge factor list (clarity, visual hierarchy, trust, ease of use, aesthetic pleasure) as question prompts ([paper](https://arxiv.org/html/2510.08783v1)). Do not trust the judge's "ease of use" score: it is systematically overrated and close to chance pairwise.
- Ground the first-screen protocol in Lindgaard (50 ms vs. 500 ms) and Reinecke (500 ms appeal) ([CHI'13](https://www.eecs.harvard.edu/~kgajos/papers/2013/reinecke13predicting.shtml)):
  - Show only the 1280 and 320 first screens.
  - Ask fixed questions: what is it, who is it for, what would you click first, what one word describes the feel.
  - A *second*, text-only grader compares the answers with the brief. This keeps visual judgment apart from the comparison with the brief.

### Layer 4: which is better

- **Pairwise, not absolute.** WebDevJudge finds pairwise beats single grading by more than 8pp ([WebDevJudge](https://arxiv.org/html/2510.18560v1)). MLLM-as-a-Judge finds pair comparison is the setting closest to humans ([paper](https://arxiv.org/abs/2402.04788)).
- **Inputs:** give the judge code plus several screenshots. In ArtifactsBench, going from no images to several screenshots added 12pp ([ArtifactsBench](https://arxiv.org/html/2507.04952v2)). WebDevJudge finds code is the most important input ([WebDevJudge](https://arxiv.org/html/2510.18560v1)).
- **Ranking statistics:**
  - Bradley–Terry with sandwich or bootstrap confidence intervals and active sampling of pairs ([Chatbot Arena](https://arxiv.org/html/2403.04132v1)).
  - Style covariates in the BT model ([style control](https://lmsys.org/blog/2024-08-28-style-control)). For UI these could be page length, number of sections, colour saturation, amount of animation, and dark vs. light.
  - UI-Bench's TrueSkill with expert raters is an alternative for the small expert panel ([UI-Bench](https://arxiv.org/abs/2508.20410)).
- **Vote hygiene:** count only votes cast blind, remove duplicate votes, and filter anomalous voters ([WebDev Arena](https://arena.ai/blog/webdev-arena), [Chatbot Arena](https://arxiv.org/html/2403.04132v1)).

### Layer 5: is it templated

- Measure the convergence Anthropic describes: fonts, purple gradients, the same picks again ([blog](https://claude.com/blog/improving-frontend-design-through-skills)). Count these directly from computed styles.
- Use the Vendi Score as the single diversity number over a similarity kernel ([Vendi](https://arxiv.org/abs/2210.02410)).
- Reuse Design2Code's block detection, which locates text by recolouring the DOM, to compare layout skeletons across briefs ([Design2Code](https://arxiv.org/html/2403.03163v3)).

### Measuring the skill itself

Copy the SkillsBench protocol ([SkillsBench](https://arxiv.org/html/2602.12670v1)):

- the same task with and without the skill;
- 5 or more runs per condition;
- Hake's normalized gain;
- per-task deltas reported, including negative ones;
- a "self-generated skill" control.

---

## 5. Where we can go deeper

### 5.1 Measure the gain from the skill, not a model ranking

Every benchmark above ranks models. We compare **one model with and without a skill**. The differences will be small and close in quality, which is the regime where judges fail:

- Position bias is worst when quality is close ([Shi et al.](https://arxiv.org/abs/2406.07791)).
- MLLM pairwise accuracy is near chance when humans rate the two as close ([MLLM as a UI Judge](https://arxiv.org/html/2510.08783v1)).

Consequences:

- **Paired design per brief.** For each brief, take k runs with the skill and k without, and compare across the pairs. Report the win rate with a bootstrap **clustered by brief**, because votes on the same brief are correlated.
- **Controls:**
  - (a) No skill.
  - (b) The skill under test.
  - (c) A **placebo skill** of the same length with generic "be careful, check your work" text. This separates "more tokens of instruction" from "design knowledge".
  - (d) Optionally, Anthropic's frontend-design skill as a public reference ([blog](https://claude.com/blog/improving-frontend-design-through-skills)).
  - SkillsBench shows long, comprehensive skills can hurt, so the placebo control matters ([SkillsBench](https://arxiv.org/html/2602.12670v1)).

### 5.2 How many pairwise votes [my calc]

These numbers are for a two-arm comparison (skill vs. no skill), two-sided α = 0.05, power 0.8, against a 50% null. They count **non-tie** votes. WebDev Arena sees about 26% ties ([blog](https://arena.ai/blog/webdev-arena)), so the right-hand column scales by 1/0.74.

| True win rate of the skill | Non-tie votes needed | Votes needed with ~26% ties |
|---|---|---|
| 70% | ~47 | ~63 |
| 65% | ~85 | ~115 |
| 60% | ~194 | ~262 |
| 55% | ~783 | ~1,057 |

The 95% confidence-interval half-width on a win rate near 50% is about:

| Votes | Half-width |
|---|---|
| 100 | ±9.8pp |
| 200 | ±6.9pp |
| 400 | ±4.9pp |
| 1,000 | ±3.1pp |

Then multiply by a design effect for clustering by brief, 1 + (m − 1)·ICC, where m is the number of votes per brief.

- **Practical target:** at least 40 briefs, at least 3 runs per arm, and the judge on every within-brief pair with both orders. This gives several hundred judge votes per skill. Spend the human votes on a stratified subsample.
- **For a multi-skill BT leaderboard:** Chatbot Arena needed ~4,400 adaptive vs. ~6,800 random samples to reach a win-matrix precision of 0.2 ([Chatbot Arena](https://arxiv.org/html/2403.04132v1)). UI-Bench used about 4,000 expert votes for 10 systems ([UI-Bench](https://arxiv.org/abs/2508.20410)). Budget about 300–400 votes per system and use active sampling.

### 5.3 Calibrating the Claude Opus judge

1. **Human calibration set.** Build 200–300 pairs labelled by several designers with rubrics, about the size used by WebCompass (200) and ArtifactsBench (280 queries).
   - Expect a low human α unless rubrics are used: 0.26–0.47 in the aesthetics studies ([Design2Code](https://arxiv.org/html/2403.03163v3), [UIClip](https://arxiv.org/html/2404.12500v1)).
   - Report judge–human agreement **against the human–human ceiling**, as WebDevJudge does (84.8%).
2. **Known-answer pairs.** Pair each page with a version degraded on purpose (UIClip's "jitter": broken spacing, clashing colours, failed contrast, overflow at 320) ([UIClip](https://arxiv.org/html/2404.12500v1)). The judge must pass these at more than 95% before a scheduled run counts. This also catches **version drift**, which ArtifactsBench hit when its judge versions changed ([repo](https://github.com/Tencent-Hunyuan/ArtifactsBenchmark)). Pin the exact Opus model ID per run.
3. **Position.** Judge every pair in both orders.
   - A pair counts as a win only if the judge agrees with itself in both orders; otherwise it is a tie.
   - Report the position-consistency rate: 83–90% for current judges ([WebDevJudge](https://arxiv.org/html/2510.18560v1)).
   - Swapping is for *measuring* bias, not *fixing* it. WebDevJudge found it barely moved agreement.
4. **Self-preference.** Both arms are Claude, so the bias does not favour one arm through authorship.
   - Hypothesis [untested]: a Claude judge may favour Claude's own *default* aesthetic, which would bias against a skill that moves away from the default. Panickssery et al. show self-preference tracks self-recognition ([paper](https://arxiv.org/abs/2404.13076)).
   - Mitigation: run a cross-family judge (Gemini or GPT) on a 20% subsample and report the gap between judges, as WebCoderBench does to limit preference leakage ([paper](https://arxiv.org/html/2601.02430v1)).
5. **Criteria leakage.** The judge's rubric must not reuse the skill's wording, for example "avoid Inter, use committed palettes". Otherwise the exam rewards obeying the skill rather than quality. Keep the rubric written by people and fixed before any skill is seen.
6. **Style covariates.** Add page length, number of sections, saturation, animation count and dark/light to the BT model. ArtifactsBench already found a bias toward length ([ArtifactsBench](https://arxiv.org/html/2507.04952v2)), and LMArena found length dominates style effects ([style control](https://lmsys.org/blog/2024-08-28-style-control)).
7. **Judge inputs.** Give code, first screen, full page, and states after interaction, at both 320 and 1280. Ask for evidence (which element, which width) before the verdict. UICrit shows grounded, bounded feedback is better ([UICrit](https://arxiv.org/abs/2407.08850)).

### 5.4 Layer 3 has no prior benchmark

No benchmark I found runs a first-screen comprehension test on generated pages. Proposed method:

- A blind viewer (the judge, or people) sees only the first screen.
- A separate text-only grader compares the answers with the brief.
- Scoring: "what is it" correct, "who is it for" correct, and "what would you click first" matches the brief's main action.
- Compare the judge with 5–10 people on a subsample. Participant numbers in the literature are only vendor guidance [unverified].
- Reinecke shows first impressions vary by age, gender and education, so record rater demographics for the human panel ([CHI'13](https://www.eecs.harvard.edu/~kgajos/papers/2013/reinecke13predicting.shtml)).

### 5.5 Layer 5 has no empirical prior

Templating is described, but has not been measured ([Shin et al.](https://arxiv.org/html/2603.13036v1), [Anthropic](https://claude.com/blog/improving-frontend-design-through-skills)). Measure at three levels:

- **Pixels:** DreamSim and CLIP similarity between first-screen screenshots ([DreamSim](https://arxiv.org/abs/2306.09344)). Validate on UI screenshots with a small set of human triplets, since DreamSim was tuned on natural images.
- **Structure:** a layout skeleton from DOM blocks (Design2Code-style), a block-sequence edit distance, and the hero pattern.
- **Tokens:** computed font families, a palette clustered in Lab, border radius, shadow and gradient use, and icon set.

Reports:

- (a) Mean similarity **across different briefs** within one arm; lower is better.
- (b) Similarity to the **no-skill centroid**: does the skill escape the default?
- (c) The Vendi Score per arm ([Vendi](https://arxiv.org/abs/2210.02410)).
- (d) A "monoculture" table: share of outputs using the same font or the same hero gradient, across all briefs. This would catch a skill that swaps one default for another, such as Inter for Space Grotesk, which the Anthropic post itself warns about.

Diversity must be read *together with* layers 1–4, so that random noise does not score as creative.

### 5.6 Making briefs hard enough that a skill cannot ace them

Evidence on what is hard:

- Fine perception of alignment, size and spacing ([FullFront](https://arxiv.org/html/2505.17399v1)).
- Subtle interactions ([Interaction2Code](https://arxiv.org/html/2411.03292v3)).
- Long, dense and non-English pages ([Design2Code-HARD](https://arxiv.org/html/2403.03163v3)).
- Framework code ([DesignBench](https://arxiv.org/abs/2506.06251)).
- Visual quality is the weakest axis everywhere ([WebCompass](https://arxiv.org/html/2604.18224v1)).
- Functional pass rates are only ~28–38% for full sites ([WebGen-Bench](https://arxiv.org/html/2505.03733)).

Concrete brief features:

- **Conflicting constraints:** a given brand palette that fails contrast unless the model adapts it; a fixed font that has no bold weight.
- **Content density:** real tables and numbers that must appear, a pricing page with 4 tiers × 12 features at 320 px, long German compound words, an RTL locale.
- **States:** empty, loading, error, long-name overflow, zero results. Most defaults show only the happy path.
- **A non-default aesthetic required by the brief:** brutalist, or Japanese high-density (Shin et al.'s example of a model overriding regional density preferences, [HTML](https://arxiv.org/html/2603.13036v1)), or a print or editorial look. Layer 2 checks the brief's style was followed, not a generic "modern" style.
  - WebGen-Bench's "modernness" criterion would *punish* this ([paper](https://arxiv.org/html/2505.03733)). Avoid such criteria.
- **Given design tokens or a reference screenshot** to conform to (WebCompass's "Style Conformance").
- **Accessibility woven into the interactions:** keyboard-operable custom widgets, focus traps in dialogs, motion that must respect reduced-motion.
- **Multi-page consistency:** 3 pages sharing one system.
- **An edit/repair round** after the first build (WebCompass, DesignBench). Skills may help less on changing existing code.
- **Real-user-style briefs:** short and underspecified, like WebDev Arena prompts ([blog](https://arena.ai/blog/webdev-arena)) and WebCoderBench's real logs ([paper](https://arxiv.org/html/2601.02430v1)). Mix them with long design documents (WebCompass).
- **Difficulty assigned after the fact** from observed results, as ArtifactsBench does ([paper](https://arxiv.org/html/2507.04952v2)). Keep a hidden held-out set and rotate it, because WebCoderBench keeps its data closed precisely to prevent gaming ([paper](https://arxiv.org/html/2601.02430v1)).

### 5.7 Reuse and licences, summarized

**Can reuse the tasks:**

- Design2Code and Sketch2Code: ODC-By, research use only.
- WebUIBench: CC-BY-4.0.
- ArtifactsBench: CC-BY-NC-4.0 on HF.
- WebGen-Bench: MIT per the paper, unclear in the repo.

These are all reference-based or app-oriented, not design briefs. They make good *seed* material for our layer 2 checklists and layer 1 interaction scripts.

**Cannot redistribute:** WebDev Arena preference data, which is gated with an empty LICENSE file.

**Not yet released:** FrontendBench data. WebCoderBench is closed.

**Open tooling worth adopting directly:**

- axe-core (MPL-2.0)
- ReDeCheck
- AIM
- DreamSim
- Design2Code metrics code (MIT)
- WebCompass code

---

## 6. Open items and things I could not verify

- WebDevJudge's "70.34%" best-agreement figure (seen only in a search snippet). In the HTML: best vanilla pairwise ~66% with ties; 82.75% non-tie with Likert guidance.
- UI-Bench's number of experts (194 is from a secondary summary only).
- Whether Design Arena uses BT or Elo, and its scale or user numbers.
- Licences of the Interaction2Code, DesignBench, FullFront and WebDevJudge code; the WebCompass data licence.
- Whether UIClip weights are released.
- The exact text of the five-second-test methodology from NN/g or Lyssna (only vendor blogs found).
- Whether DreamSim or CLIP similarity tracks human similarity *for UI screenshots* (no study found; worth a small validation of our own).
- Any controlled study linking Lighthouse or axe scores to human preference on generated pages (none found).
