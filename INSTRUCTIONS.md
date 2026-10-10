# INSTRUCTIONS: Search in Whose Language?
## Separating the query gap from the evidence gap for search agents in Indic languages

You are a Claude Code agent running a complete research project in this folder, start to
finish, without waiting for the user between phases. Your user is Mohammed Abraar (author name
on the paper; email abraar@vizz.vizuara.ai; GitHub `Abraar237`, already logged in via `gh`).
This file is your complete brief. Read it fully before doing anything. Predecessor projects
called this file `MISSION.md`; it plays the same role.

Target: a **workshop-level paper** (8 pages + appendix, ICLR style) that is unique, honest and
reproducible, plus the public repo, the project website, the explainer film and three GIFs.
Hard budget: **$30 of API spend** (hard stop $24, see §4).

TIMING (binding): the MAST @ FIRE 2026 shared task has an Indic track whose working notes
are due **2026-10-15**; participants may publish query-translation analyses as side results.
Move fast and pin the contribution to the two things nobody has (§1.1).

---

## 0. THE CHECKPOINT PROTOCOL

The user has authorised running CP1 through CP6 **without stopping** (2026-10-10): "continue
until he completes all the research ... paper, video, github website etc." Record each CP in
`MILESTONES.md` as it completes and report ONCE at the end with links, headline numbers, spend
and the reviewer score. Stop early only for a hard blocker:

- a pre-emption discovered at CP1 (a paper that already owns the exact decomposition in §1.4),
- the cost tracker's hard stop, an exhausted key, or a provider that refuses all calls,
- a result that makes the paper impossible to write honestly (then write the null and say so).

| CP | Gate | Done when |
|---|---|---|
| CP1 | Lit review + pre-emption | `lit_review/LIT_REVIEW.md` with verdict, novelty table, 40+ verified refs |
| CP2 | Experiment plan frozen | `EXPERIMENT_PLAN.md` + `site/plan.html`; budget table from a measured pilot; directions dated in `MILESTONES.md`; corpus and question bank frozen with SHA-256 |
| CP3 | Experiments + analysis | all runs, `experiments/analyze.py` -> `results/analysis.json` |
| CP4 | Paper | ICLR dual build compiles, figures, 40+ verified citations, appendix with verbatim prompts |
| CP5 | Published | public repo, GitHub Pages site, film on the site, 3 GIFs |
| CP6 | Self-review | `REVIEW.md` from `a-star-reviewer` with scores, P(accept), ranked fixes -> REPORT TO USER |

---

## 1. THE PROBLEM

### 1.1 Why this matters, and what is ours

Search agents (an LLM that iteratively writes queries, reads results and answers) are now the
default way hundreds of millions of people in India reach the web through chat products. When
the user asks in Hindi, Telugu or Bengali, accuracy drops relative to the same question in
English. Two very different causes produce the same drop, and the fixes are different:

- the **query gap (QG)**: the agent's own behaviour. It writes worse queries, or searches in a
  language where the evidence is not (English queries for a fact that only Hindi Wikipedia
  records, or Hindi queries for a fact that only English Wikipedia records);
- the **evidence gap (EG)**: the web itself. Hindi Wikipedia has 2.4% of English's articles,
  Telugu 1.8%; Hindi is 0.2% of Common Crawl pages. Even a perfect query finds nothing.

If QG dominates, prompting and training fix it. If EG dominates, only cross-lingual search
(crossing to English evidence) or content creation fixes it. Nobody has separated them.

What exists (full sweep: `lit_review/00_preemption_sweep_2026-10-10.md`, verdict
ALIVE-BUT-CROWDED): XBCP (2606.15345) runs deep-research agents on a BrowseComp-Plus corpus
translated into 12 languages with an oracle-retrieval decomposition, but the question is
always English, the agent's query language is never measured or forced, and there is no Indic
language. MarathiWeb (SIGIR 2026) evaluates two web-search LLMs on native Marathi queries and
attributes failures to integration "rather than missing sources" by inspection, one language,
no manipulation. DELTA (2601.02956) names a "gold-availability prior" for single-shot RAG on
MKQA and corrects it statistically, no agent, no Indic. The Aug-2026 failure taxonomies
(2608.01913, SearchAuditor, CIVI) split retrieval gap from utilisation gap in English only.
**A paper whose claim is only "agents do worse on Hindi and oracle evidence closes the gap" is
DEAD (XBCP and MarathiWeb already say it).**

**Ours alone, and the paper lives or dies on these two:**
1. **The agent's query language as a measured mediator and then a manipulated factor.** Log
   the script of every search call under a free policy, then force the policy (match /
   english / dual) and measure recovery, on an evidence pool whose language we control.
2. **A coverage x conditional-accuracy decomposition** of the real-world gap:
   `Acc_L = Cov_L * Acc(L | evidence in L) + (1 - Cov_L) * Acc(L | evidence only in English)`,
   where `Cov_L` is measured on live Indic Wikipedia and the conditional accuracies come from
   the controlled experiment. This turns "Hindi is worse" into "x points are the web, y points
   are the agent, z points are recoverable by searching in both languages".

Name the terms **query-side gap (QG)**, **evidence-side gap (EG)** and the residual under
oracle evidence the **integration gap (IG)**. Do not reuse "retrieval gap" (2608.01913 owns it).

### 1.2 Core questions

1. Under a free policy, in what language do agents search when the question is in an Indic
   language, and does that choice track where the evidence is?
2. Holding content fixed (parallel questions) and the evidence pool fixed, how much of the
   Indic-vs-English accuracy drop is QG, how much EG, how much IG?
3. Does forcing the query language (match / english / dual) recover QG, and does the sign of
   the "search in English" lever flip with where the evidence lives (the policy x evidence
   interaction that reconciles Amiraz 2507.07543 with Ranaldi 2504.03616)?
4. In the wild, is the coverage term or the agent term bigger, and does that differ between
   Hindi and a lower-resource language (Telugu or Tamil)?

### 1.3 Design (refine and freeze at CP2; API-only for the agents, local or Modal for retrieval)

**Languages.** Hindi (hi) and Telugu (te) as the primary pair (both in MIRACL, TyDi/XOR-TyDi
and IndicGenBench; Telugu Wikipedia is 1.8% of English). Tamil or Bengali as a third if
spend stays under $12 after the primary grid. Use ISO codes everywhere.

**Question bank** (target 120-150 items per language, parallel en/L, gold answer with
aliases, gold evidence location known by construction; frozen with SHA-256 before any call):

| Source | Why | Evidence condition it supplies |
|---|---|---|
| MLQA-hi (1910.07475) | the only set whose hi/en gold paragraphs are genuinely parallel Wikipedia text | evidence in BOTH |
| IndicGenBench XorQA-In / XOR-TyDi te, bn (2404.16816, 2010.11856) | human-written Indic questions whose gold is an English Wikipedia passage; locate the Indic counterpart via Wikidata sitelinks and check whether the answer string occurs | evidence EN-only (and BOTH when it does) |
| MultiLoKo local hi/te/ta (2504.10356) or IndicQuest v2 (2608.15535) | locally-sourced India-centric questions whose natural evidence is Indic; verify the Indic gold passage by hand | evidence in L (and L-only when English lacks it) |

Exclude locale-dependent answers (XLQA 2508.16139). Translate missing parallel questions
with one model and back-translate with another; keep only items where the back-translation
preserves the answer; report the kept fraction. Run a **closed-book arm** (no search tool) on
every item for parametric leakage and report the attribution rate (Muller 2305.14332: up to
half of correct XOR-TyDi answers are not attributable to retrieved passages).

**Evidence pool E** (offline, reproducible, the primary instrument): chunked articles from
the HF dataset `omarkamali/wikipedia-monthly` snapshot 20261001 (hi 186k articles, te 146k,
en 7.27M; use the English articles that are sitelink-aligned to the hi/te pools plus a
sampled distractor set of ~300k English chunks so the English pool is realistic but
indexable). Align same-entity articles through Wikidata sitelinks. Conditions:

| E | Pool served by the search tool |
|---|---|
| EN-only | English chunks only |
| L-only | Indic-language chunks only |
| BOTH | union, one index, language tag on every hit |
| NONE | tool returns nothing relevant (50-item subset): floor, and a refusal/hallucination check |

Retrievers: BM25 (`bm25s`, custom Unicode-script-aware tokenizer; no stemming for Indic) as
the primary, and one multilingual dense retriever (`BAAI/bge-m3`, MIT licence) as the second
(single-retriever designs die in review). Embed on Modal (profile `thesreedath`; the Starter
plan has a $30/month free credit; if the workspace spend limit blocks it, as happened to the
voice project, embed on the local M4 overnight; bge-m3 on ~500k chunks is feasible on CPU).
Expose one tool to the agent: `search(query: str, lang: "hi"|"te"|"en"|"any") -> top-5
chunks (title, language, text)`. Cache every retrieval result on disk so re-runs are free.

**Agent.** A fixed ReAct loop: up to 4 search calls, then a final answer; system prompt and
tool schema identical across conditions except the policy sentence; temperature 0;
`reasoning: {effort: "minimal"}` with `max_tokens` headroom; one episode per process, turns
sequential. Log every query string, its detected script (Unicode block ranges: Devanagari,
Telugu, Bengali, Latin, mixed), the `lang` argument the agent chose, the hits and whether the
gold chunk was among them.

**Factors.**
- Question language **Q** in {en, L}.
- Query policy **P** in {free (log the choice), match (query in the question's language),
  english (translate and query in English), dual (both languages every call)}.
- Evidence pool **E** in {EN-only, L-only, BOTH} (+ NONE subset).

Core cells, fractional: for Q=L run all P x E (12 cells); for Q=en run P in {free, match} x E
(6 cells); P=dual only where it is informative (E=BOTH and E=L-only). That is ~16 cells x
~130 items x 2 languages = ~4,200 episodes per model at ~5-8k tokens per episode. Pilot 10
items per cell first and write the measured cost into `EXPERIMENT_PLAN.md`.

**Models** (3 families via OpenRouter; re-fetch prices at CP2 from
`https://openrouter.ai/api/v1/models`; 2026-10-10 list prices per 1M input tokens):

| Family | Candidate id | Why |
|---|---|---|
| Google | `google/gemini-2.5-flash-lite` ($0.10) or `google/gemini-3.1-flash-lite` ($0.25); `google/gemini-3.6-flash` ($0.75) only on a subset | strong Indic coverage; the predecessor projects' main family |
| OpenAI | `openai/gpt-5-mini` ($0.25) or `openai/gpt-5.6-luna` ($0.20) | second closed family |
| Anthropic | `anthropic/claude-haiku-5.5` ($0.10) | third closed family |
| Open-weight | `google/gemma-4-31b-it` ($0.09; a `:free` route also exists but is rate-limited and unmetered, do not use it for the paper) | an open model with Indic pretraining; no Modal GPU needed. No Indic-specialised model (Sarvam, Krutrim) is on OpenRouter as of 2026-10-10; if the user supplies one, add it |

Run the full fractional grid on two cheap families, the Q=L x E=BOTH x P={free, dual} slice
plus the symmetric monolingual check on the other two.

**Oracle and controls.**
- **Oracle evidence**: the gold chunk given directly, Q=en vs Q=L, no search: the integration
  gap (IG) and the reading ceiling.
- **Closed-book**: no tool; parametric leakage and attribution rate.
- **Symmetric monolingual check**: Acc(Q=en, EN-only, match) vs Acc(Q=L, L-only, match),
  under BM25 and under bge-m3: the Indic-script retrieval + reading cost with evidence present.
- **Repeat-call noise floor**: 30 items x 5 identical runs in one cell (temperature 0 is not
  deterministic on these routes).
- **Judge**: alias-aware exact match / token-F1 in both scripts first; an LLM judge (a model
  not under test) only on disagreements; hand-audit n >= 40 judged items across languages and
  ship `results/audit_sample.json`.
- **Coverage in the wild (`Cov_L`)**: for every item, does live L-Wikipedia (the 20261001
  snapshot) contain a sentence supporting the gold answer? Sitelink + answer-string check,
  then a 50-item manual spot-check. This is the weight in the decomposition.

**Estimands (one `analyze.py`, seeded, byte-identical on re-run).**
- Total gap: Acc(Q=en, BOTH, free) - Acc(Q=L, BOTH, free).
- **QG** = that gap with evidence present in both languages; mediator = share of English
  search calls under free and gold-hit rate per call; **recoverable QG** = gain from P=dual
  (and P=english) at E=BOTH.
- **EG (controlled)** = Acc(Q=L, BOTH) - Acc(Q=L, L-only) and Acc(Q=L, BOTH) - Acc(Q=L,
  EN-only); the P x E interaction tells whether forcing English helps (EN-only) or hurts
  (L-only).
- **IG** = Acc(Q=en, oracle) - Acc(Q=L, oracle).
- **Decomposition in the wild** per language and model: plug Cov_L and the conditional
  accuracies into the formula; report each term with a bootstrap CI.
- Statistics: unit = item; paired within-item contrasts; sign-flip permutation (20k)
  clustered by source dataset; item-cluster bootstrap 95% CIs (10k); interactions (P x E,
  language x model) by label permutation; Benjamini-Hochberg over the full family from day
  one, bold survivors only; noise floor beside every headline.

### 1.4 Pre-registered directions (copy into `MILESTONES.md` with today's date BEFORE any data)

- **D1 (query-language drift).** Under P=free with Q=L, the closed-model agents issue English
  queries in more than half of search calls; the share is higher for Telugu than for Hindi.
- **D2 (QG exists and is partly recoverable).** Acc(Q=en, BOTH) - Acc(Q=L, BOTH) > 0;
  P=dual recovers at least half of it; P=english recovers less than P=dual (the XRAG union
  effect, 2505.10089).
- **D3 (policy x evidence interaction).** Forcing English queries helps when E=EN-only and
  hurts when E=L-only; the interaction is significant after BH.
- **D4 (coverage dominates in the wild for the lower-resource language).** Cov_te < 0.5 and
  Cov_hi > Cov_te; the coverage term of the decomposition exceeds the agent term for Telugu
  but not for Hindi.
- **D5 (the retriever carries the symmetric gap).** The hi/te deficit in the symmetric
  monolingual check is larger under BM25 than under bge-m3 and shrinks under oracle passages.
- **D6 (IG is small for closed models).** Under oracle evidence, Q=L is within 5 points of
  Q=en for the closed families (contrast XBCP, where translated evidence still hurts).

Falsification: D1 fails if free-policy query language tracks the question language; D3 fails
if P=english helps uniformly; D4 fails if Cov_L > 0.7 for both languages. If a direction
fails or reverses, report it plainly in the abstract.

### 1.5 Pre-emption frontier (verified 2026-10-10; re-verify at CP1 and delineate in the paper)

| Nearest work | What it does | What it does NOT do (ours) |
|---|---|---|
| XBCP (2606.15345) | Deep-research agents on a fixed corpus translated into 12 languages; oracle decomposition into retrieval vs integration | question always English; query language never measured or forced; no Indic; translated, not native, evidence |
| MarathiWeb (Kale, SIGIR 2026) | Two web-search LLMs on native Marathi local vs global queries; failures attributed to integration by inspection | one language, two models, live web only; evidence availability observed, not manipulated; no parallel English arm |
| MAST @ FIRE 2026 Indic track (Thakur et al.) | 9 Indic query languages over the English BrowseComp-Plus corpus; iterative agents | English-only corpus, so EG is zero by construction; a systems shared task, not attribution |
| DELTA (2601.02956, ACL 2026 Findings) | Names the gold-availability prior; regression debiasing; English pivot vs fused query | single-shot RAG on MKQA; no agent, no Indic, no pool manipulation |
| Diagnosing Search Behavior and Failure Modes (2608.01913) | retrieval gap vs utilisation gap with oracle evidence, 6 agents | English only; retrieval gap not split into query vs corpus |
| Cross-Lingual Cost (2507.07543), XRAG (2505.10089), tRAG/CrossRAG (2504.03616), CORAL (2604.25676) | query-language vs document-language effects in RAG; one controlled Google ablation; an agent that picks the corpus language | non-agentic or end-accuracy only; no Indic; no decomposition |
| Better To Ask in English? (2504.20022), IndicKLAR (2605.29637), MultiLoKo (2504.10356) | parametric Indic knowledge gaps, closed-book | no retrieval, no agent |

### 1.6 Threats to pre-empt in v1

Parametric leakage (closed-book arm, attribution rate). Translation artefacts in parallel
questions (back-translation filter, kept fraction reported, GAIA-v2-LILT 2604.24929 warns
that Hindi agent gaps are partly translation artefact). Wikipedia is not the web (say so;
the optional live arm in §1.7 is the external-validity check). Chunking and index-size
asymmetry between English and Indic pools (report pool sizes; the symmetric monolingual check
isolates it). Script detection on code-mixed or transliterated queries (classify "mixed" and
report its share). Judge bias across scripts (alias-aware EM first, audit shipped).

### 1.7 Optional live-web arm (only if a key exists; never the primary instrument)

The user has not provided a web-search API key. If one is added to `.env` later
(`PERPLEXITY_API_KEY` for the Perplexity Search API at $1 per 1,000 fast requests with
`search_language_filter` and `country`, the only cheap engine with a language filter), run the
Q=L x P=free cell on 100 items per language live, log query scripts and cited-source
languages, and report it as external validity. Without a key, skip it and say so in
Limitations. Do not use OpenRouter `:online` (Exa, $7 per 1,000 and no language control) for
anything but a 20-call sanity check.

---

## 2. THE PIPELINE (copy the predecessors; it has worked five times)

Predecessor papers are in `reference/` (script-bias, voice-judge, ocr-injection,
schema-drift). Templates copied from the most recent project are in `templates/` (runner,
cost tracker, analysis script, figure style, LaTeX dual build, site, film builder, TTS, plan
page, lit review, reference verification, review). **Read `reference/` and `templates/`
first.** The script-bias paper is the closest sibling in spirit (Indic scripts, matched items,
honest audits).

| Stage | Replicate | Skill (in `Agent Skills/`) |
|---|---|---|
| 1. Lit review | Start from `lit_review/00_preemption_sweep_2026-10-10.md`; 3-4 angle agents + a recency sweep for anything after 2026-10-10 (and the MAST working notes after 2026-10-15); verified CSV + `LIT_REVIEW.md` with the novelty-delineation table written BEFORE results | `prior-work-check` |
| 2. Plan | `EXPERIMENT_PLAN.md` + `site/plan.html`; budget table from a measured 10-item pilot; pre-registered directions dated in `MILESTONES.md` | `paper-topic-selection`, `research-pipeline` |
| 3. Experiments | Frozen question bank and corpus (SHA-256 manifests); `build_corpus.py`, `index.py`, `search_tool.py`, `agent.py`, `indic_runner.py` (one episode per process, randomised item order, resume-safe JSONL keyed by model x item x Q x P x E x rep); `cost_tracker.py` with hard stop; one `analyze.py` -> `results/analysis.json`; EVERY paper number traces to it | — |
| 4. Paper | ICLR-format LaTeX from day one (`templates/iclr_latex_template/`); anonymous + named dual build from one body; 40+ arXiv-verified refs (`templates/refs_verification_example.md`); HTML->headless-Chrome teaser figure (the decomposition as a stacked bar per language); results tables with CIs, bold BH survivors; verbatim prompts, the tool schema and one full episode per policy in the appendix; Indic text rendered with a Unicode-capable font (Noto Sans Devanagari / Telugu via fontspec or XeLaTeX-compatible tectonic build) | `research-paper-writing`, `paper-quality`, `paper-figures`, `humanizer`, `no-ai-slop` |
| 5. Publish | Public repo under `Abraar237` (`.gitignore` BEFORE first add; `.env` never committed; `Agent Skills/`, `reference/`, `templates/`, `corpus/raw/`, `corpus/index/` excluded; the corpus regenerates from the HF snapshot and the scripts); GitHub Pages from `docs/`; film (ElevenLabs Matilda `XrExE9yKIg1WjnnlVkGX`, script written first, -14 LUFS, CONTINUOUS animated motion, numbers from `analysis.json`; `templates/build_film_example.py`); 3 GIFs in the CLEAN FLAT CHART style (white card, flat bars, monospace numerals, replay pill, Helvetica; NOT hand-drawn rough.js, the user rejected that look) | `research-website`, `paper-site`, `paper-to-video`, `research-film`, `social-media-gif` |
| 6. Review | `a-star-reviewer` with its calibration data on the final PDF; report scores, P(accept), effort-ranked fixes; then `venue-fit` for a workshop shortlist (multilingual / low-resource NLP and agent workshops) | `a-star-reviewer`, `venue-fit`, `format-linter` |

Install the skills once at start: `cp -R "Agent Skills/3-research-paper-writing/skills/"* ~/.claude/skills/`
(and the same for bundles 1, 2 and 4). Most are already in `~/.claude/skills/`.

---

## 3. METHOD LESSONS FROM THE PREDECESSORS (do not relearn the hard way)

1. **One episode per process, randomised order, temperature 0, resume-safe JSONL.** Cache
   retrieval results on disk so only LLM calls cost money.
2. **Pre-register in writing before data; report reversals plainly.**
3. **Single-anything dies in review.** Two languages minimum, three question sources, two
   retrievers, three model families, two paraphrases where translation allows, a repeat-call
   noise floor from day one.
4. **Test interactions directly.** A difference in significance is not a significant
   difference. D3 is an interaction; test it as one.
5. **BH over the full family from day one; bold only survivors.**
6. **Hand-audit n >= 40 judged answers across scripts** and ship the audited sample. Never
   claim an audit you did not perform. The script-bias paper's Hinglish audit is the model.
7. **Verify every citation** via arxiv.org/abs (or the arXiv API; Semantic Scholar batch when
   arXiv rate-limits). Items in the sweep marked UNVERIFIED stay out until verified.
8. **Cost tracker with hard stop; log `usage.cost` exactly.** Reasoning tokens bill as output:
   `reasoning: {effort: "minimal"}` (or `low` where minimal is rejected) with `max_tokens`
   headroom, or you get empty replies.
9. **Corrected-numbers discipline:** when a number changes, update paper, site, film and GIFs
   in ONE pass.
10. **Figures:** Times in paper figures, white backgrounds, house palette (slate #155e8c, hot
    #b3006b, shelf #c0641a, good #1c7a55), eyebrow titles, direct labels, the finding
    annotated on the figure; `templates/figure_style.py`. Indic glyphs need a Noto font in
    matplotlib; test one Devanagari and one Telugu label early.
11. **Pre-empt the reviewer in v1:** noise floors, interaction tests, per-family tables, BH,
    verbatim prompts, honest Limitations (Wikipedia is not the web; two languages; closed
    models change).
12. **Lessons from the two newest reviews (psb1 v5, voice provenance):** explain the headline
    mechanism, do not just observe it (the query-script log and the gold-hit rate per call
    are the mechanism); never let a comparison be confounded by information content (parallel
    questions, same pool); give the lever's cost where it was not needed (P=dual doubles
    search calls; report tokens and latency); a result on one family is a result on one
    family.
13. **Pilot first** (`--limit 10` per cell), read the raw episodes in both scripts, confirm
    the script detector and the judge, then scale.

---

## 4. BUDGET (hard rules)

- **Cap $30. Hard stop $24 in `cost_tracker.py`.** The OpenRouter key is shared with the
  sibling project (`../cache layout cost research/`) and held $49.72 on 2026-10-10, so the two
  projects' hard stops must sum to less than that. If the user tops up, raise to $25.
- Expected (confirm with the pilot, then write the table into `EXPERIMENT_PLAN.md`): two
  cheap families on the full fractional grid (~4,200 episodes x ~6k tokens each) ~$6-10; two
  more families on the headline slice ~$3-5; closed-book, oracle and noise-floor arms ~$2;
  judge disagreements ~$1; question translation and back-translation ~$1; retrieval $0
  (local BM25) plus Modal free credit or local CPU for bge-m3.
- Report spend at every CP in `MILESTONES.md`. If a planned arm would break the cap, cut
  items per cell and say so in the paper; never silently exceed.

## 5. KEYS AND ACCOUNTS (`.env` in this folder; NEVER commit, never print values)

- `OPENROUTER_API_KEY`: ALL LLM calls (agents, translation, judge). Check remaining credit
  before big runs with `GET https://openrouter.ai/api/v1/auth/key` (`limit_remaining`).
  `usage.cost` in every response is the billed USD.
- `token-id` / `token-secret`: Modal (profile `thesreedath`) for bge-m3 embedding only.
  `python3 -m modal profile current` should print `thesreedath`.
- `ELEVENLABS_API_KEY`: film narration only (Matilda `XrExE9yKIg1WjnnlVkGX`). TTS-scoped:
  do NOT call `voices_read` or `user_read` (401); call text-to-speech directly
  (`templates/film_tts_example.py`).
- GitHub: `gh` CLI authenticated as `Abraar237`. Create the repo public at CP5.
- No Gemini direct key and no web-search key are provided; see §1.7.

## 6. FOLDER LAYOUT

```
indic search gap research/
  INSTRUCTIONS.md     <- this file (the brief)
  CLAUDE.md           <- pointer to this file for new sessions
  MILESTONES.md       <- checkpoint tracker; pre-registered directions go here first
  EXPERIMENT_PLAN.md  <- written and frozen at CP2
  REVIEW.md           <- written at CP6
  .env  .env.example  .gitignore
  Agent Skills/       <- the 4 skill bundles (gifs, video, writing, review)
  reference/          <- four predecessor papers; read first
  templates/          <- copied working code from the newest predecessor; adapt, do not import
  lit_review/         <- 00_preemption_sweep_2026-10-10.md (seed), angle files, lit_review.csv, LIT_REVIEW.md
  corpus/             <- items.json (question bank), coverage.json (Cov_L), manifest with SHA-256; raw/ and index/ regenerate and are git-ignored
  experiments/        <- build_corpus.py, index.py, search_tool.py, agent.py, prompts.py, indic_runner.py, cost_tracker.py, judge.py, analyze.py
  results/            <- raw/<model>.jsonl, retrieval_cache/, spend.json, analysis.json, audit_sample.json
  paper/iclr/         <- dual build;   figures/ <- build_figures.py, build_gifs.py, fig1_teaser.html
  site/plan.html      <- CP2 plan page;   docs/ <- GitHub Pages site, both PDFs, film, GIFs
  video/              <- tts.py, build_film.py, words.json, film_final.mp4
```

## 7. FIRST ACTIONS WHEN YOU (the new session) START

1. Read this file fully, then `lit_review/00_preemption_sweep_2026-10-10.md`, then the four
   PDFs in `reference/` (method and honest-reporting register), then skim `templates/`.
2. Install the skills (see §2). Confirm `tectonic`, `ffmpeg`, `node` (Remotion), `gh auth
   status`, `python3 -m modal profile current`, and `pip install bm25s datasets` (plus
   `FlagEmbedding` or `sentence-transformers` for bge-m3).
3. Sanity-check the key: one tiny OpenRouter call per planned model with a Hindi and a Telugu
   prompt; confirm `usage.cost` appears and the reply is in the right script. Log the cost.
   Record remaining credit in `MILESTONES.md`.
4. Write the pre-registered directions D1-D6 into `MILESTONES.md` with today's date.
5. CP1: extend the sweep (recency check on arXiv for anything after 2026-10-10: "multilingual
   search agent", "Indic deep research", "query language agent retrieval", "MAST FIRE 2026"),
   build `lit_review.csv` with 40+ verified ids, write `LIT_REVIEW.md` with the novelty
   table. If a paper now owns §1.1's two contributions exactly, STOP and report.
6. CP2 onward per §0. Do not stop between checkpoints. Report once at the end.

## 8. DEFINITION OF DONE (all of these, then report)

- [ ] `results/analysis.json` regenerates byte-identically; every paper number traces to it
- [ ] Paper: anonymous + named PDFs, 8 pages main + appendix, 40+ verified refs, teaser figure
      (the decomposition per language as stacked bars: QG / EG / IG / recoverable), query-script
      figure, P x E interaction figure, BH table, Limitations, Ethics/Reproducibility statements
- [ ] Repo public under `Abraar237`, README with reproduce commands and metered spend
- [ ] GitHub Pages site with story-driven sections, both PDFs, film embed, 3 GIFs
- [ ] Film 2-4 min, 1080p60, Matilda narration, -14 LUFS, continuous motion, QA contact sheet
- [ ] `REVIEW.md` with three reviewer scores, calibrated P(accept), ranked fixes, and a
      workshop shortlist from `venue-fit`
- [ ] `MILESTONES.md` spend log complete; final spend < $24
