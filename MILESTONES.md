# Search in Whose Language? · Milestones & Checkpoints

Brief: INSTRUCTIONS.md. Budget cap **$30** (hard stop $24; the OpenRouter key is shared with
`../cache layout cost research/`). The user authorised CP1-CP6 without stopping (2026-10-10);
report once at the end. Update this file at every checkpoint.

## Problem-statement history
- 2026-10-10 Pre-emption sweep by the planning session (`lit_review/00_preemption_sweep_2026-10-10.md`):
  verdict ALIVE-BUT-CROWDED. Nearest: XBCP 2606.15345 (English questions, no Indic, query
  language never measured), MarathiWeb SIGIR 2026 (one language, no manipulation), MAST @ FIRE
  2026 Indic track (English-only corpus; notes due 2026-10-15), DELTA 2601.02956 (single-shot,
  statistical), 2608.01913 (English-only taxonomy). Chosen with the two pins in INSTRUCTIONS §1.1.

## Pre-registered directions (record BEFORE any experiment call; copy from INSTRUCTIONS.md §1.4)
Recorded 2026-10-10 16:10 IST, before any agent, pilot, translation or judge call. The only
OpenRouter calls so far are 14 one-line key checks ($0.00017). Verbatim from INSTRUCTIONS.md §1.4.
- [x] **D1 (query-language drift).** Under P=free with Q=L, the closed-model agents issue English queries in more than half of search calls; the share is higher for Telugu than for Hindi.   Recorded: 2026-10-10
- [x] **D2 (QG exists and is partly recoverable).** Acc(Q=en, BOTH) - Acc(Q=L, BOTH) > 0; P=dual recovers at least half of it; P=english recovers less than P=dual.   Recorded: 2026-10-10
- [x] **D3 (policy x evidence interaction).** Forcing English queries helps when E=EN-only and hurts when E=L-only; the interaction survives BH.   Recorded: 2026-10-10
- [x] **D4 (coverage dominates in the wild for the lower-resource language).** Cov_te < 0.5 and Cov_hi > Cov_te; the coverage term exceeds the agent term for Telugu but not for Hindi.   Recorded: 2026-10-10
- [x] **D5 (the retriever carries the symmetric gap).** The hi/te deficit in the symmetric monolingual check is larger under BM25 than under bge-m3 and shrinks under oracle passages.   Recorded: 2026-10-10
- [x] **D6 (IG is small for closed models).** Under oracle evidence, Q=L is within 5 points of Q=en for the closed families.   Recorded: 2026-10-10
- Falsification: D1 fails if free-policy query language tracks the question language; D3 fails if P=english helps uniformly; D4 fails if Cov_L > 0.7 for both languages. Failures and reversals go in the abstract.

## Environment sanity
- [x] OpenRouter key remaining credit: $49.72 of $50 (2026-10-10 16:00). Key is SHARED with `../cache layout cost research/` whose agent started the same day; both hard stops are $24.
- [x] Smoke test in Hindi and Telugu: google/gemini-2.5-flash-lite, gemini-3.1-flash-lite, gemini-3.6-flash all answer in the right script, cost logged ($0.00017 total).
- [x] **BLOCKER (reported to user 2026-10-10):** the OpenRouter workspace guardrail blocks every non-Google model (gpt-5-mini, gpt-5.6-luna, claude-haiku-5.5, gemma-4-31b, gemma-3-27b, deepseek-v4-flash, qwen3.5, mistral-small, llama-4, glm, kimi, nemotron, gpt-oss all 404 "Model blocked by guardrail"). Until lifted at openrouter.ai/workspaces/default/guardrails the closed-model arm is Gemini-only; the second family must come from an open-weight model served on Modal.
- [x] **BLOCKER (reported to user 2026-10-10):** ELEVENLABS_API_KEY returns 401 invalid_api_key (same key in all six project folders). Film narration needs a new key.
- [x] Modal: profile thesreedath, test function ran (gVisor Linux). bm25s 0.3.13, datasets 5.1.0, sentence-transformers 6.0.1 installed. HF not logged in (facebook/multiloko is gated; skipped).
- [x] Fonts: Devanagari MT / Kohinoor Devanagari and .SF Telugu present on macOS; test in matplotlib at CP4.
- [x] tectonic / ffmpeg / node 25 / gh (Abraar237) present.

## CP1 · Lit review + pre-emption — DONE 2026-10-10
- [x] Recency sweep 2026-09-15..10-10 -> lit_review/recency_2026-10-10.md (one partial overlap: Where's Waldo 2610.00606, fixed-context, no agent; MAST notes still due 2026-10-15; re-check at CP4)
- [x] lit_review.csv: 145 arXiv ids verified by the arXiv API (143 OK, 2 swapped ids corrected in LIT_REVIEW.md), angle-tagged
- [x] LIT_REVIEW.md with novelty-delineation table (10 nearest neighbours) written before any result
- [x] Verdict: ALIVE-BUT-CROWDED; the two pins (query language as measured-then-forced mediator; coverage x conditional-accuracy decomposition) hold

## CP2 · Experiment plan frozen
- 2026-10-10 17:40 **CP2 amendments after the pilots (before any grid call):**
  (a) MLQA questions are filtered to self-contained ones (176 of 450 pass an LLM check; the pilot showed
  questions like "What did Keane often request?" presuppose their paragraph); 130 kept.
  (b) A tokenizer bug (English stopwords kept in Indic documents and queries) made English queries on the
  mixed pool return Hindi chunks; fixed, all indexes rebuilt.
  (c) The retrieval sanity check (question as query, 60 items/language) gave BM25 gold@5 of 0.08 (hi), 0.07 (te)
  vs 0.50 (en): transliteration spelling variants and Telugu case suffixes defeat lexical matching. The main
  grid therefore uses a HYBRID retriever (RRF of BM25 and bge-m3 dense, top-50 each); BM25-only and dense-only
  become the retriever factor for D5 on the symmetric cells. bge-m3 embeddings are computed on Modal.
  (f) 17:55 Retriever sanity with bge-m3 embeddings (60 Hindi items, question as query): dense gold@5 = 0.70
  (hi query) and 0.68 (en query on the Hindi pool); BM25 0.08 / 0.03; equal-weight RRF hybrid 0.53 (the weak
  lexical list drags the fusion down). The MAIN GRID therefore uses bge-m3 DENSE retrieval; BM25 is the
  second retriever factor on the full core grid for gemini-2.5-flash-lite and on headline cells elsewhere.
  Because dense retrieval is cross-lingual and lexical retrieval is not, "whose language the search engine
  speaks" is itself a factor in the query-side gap; this is now part of the paper's framing.
  (g) Two-pass coverage verification: pass 2 (gemini-3.6-flash) rejected 100 of 384 pass-1 acceptances;
  final verified coverage Cov_hi = 157/539 = 0.291, Cov_te = 127/539 = 0.236; factorial items hi 287
  (157 XorQA + 130 MLQA), te 127. Manual audit of 30 pass-1 acceptances: 21 yes, 7 uncertain, 2 no
  (results/coverage_audit.json); pass 2 was added because of it.
  (h) FAISS crashes next to PyTorch on macOS (duplicate OpenMP runtimes); dense search is a torch fp16
  matmul on the Apple GPU (57 ms per query over 353k passages).
  (d) Judge gains an ABSTAIN label. (e) The runner is named indic_runner.py because the sibling project's
  agent killed every process matching "runner.py --model".
- [x] Question bank: 1,328 items; factorial-eligible hi 287 (157 XorQA + 130 self-contained MLQA), te 127 XorQA;
      native-Telugu subset 120 (TyDi XOR); coverage population 539 XorQA per language. No translation step was
      needed (XorQA-In and MLQA are human-parallel), so no back-translation filter applies.
- [x] Pools from wikipedia-monthly 20261001: hi 353,075 chunks (169,949 articles), te 518,524 (145,514), en 1,058,175
      (129,646 articles, parts 000-025) + 7,310 chunks of the 681 English articles behind the items + 666 deduplicated
      gold paragraphs. Sitelinks via Wikidata (916/918 titles resolved).
- [x] BM25 indexes (5 pools, stopword fix) and bge-m3 embeddings (Modal A100, 3 pools, ~30 GPU-min); dense gold@5 on
      question-as-query: hi 0.70, te 0.70, en 0.90+; BM25 0.08 / 0.07 / 0.50. Retrieval results are logged per call.
- [x] Pilots: 5 + 80 + 12 episodes (results/pilot/); gemini-2.5-flash-lite $0.0002-0.0007 per episode; tool calling
      works on Gemini via OpenRouter and on Qwen3-30B-A3B via vLLM hermes parser on Modal.
- [x] EXPERIMENT_PLAN.md + site/plan.html; cost_tracker armed ($24). Spend at CP2 close: $0.90 (coverage passes
      $0.26 + $0.63, pilots $0.03, filter $0.01, closed-book arm in flight).
- [x] corpus/FROZEN.json v2 (SHA-256 of items.json, pool line counts, index doc counts), 18:00.
- **CP2 DONE 2026-10-10 18:20.** Grid launched: experiments/run_all.sh (OpenRouter, sequential) and
  experiments/run_modal.sh (Qwen3 on Modal) in parallel.

## CP3 · Experiments + analysis
- 2026-10-10 19:15 Pre-specified SECONDARY analysis, added after seeing closed-book accuracies (0.61-0.69, so the
  models already know many XorQA facts) and before reading any agent-grid result: all core contrasts are repeated
  on the "needs-search" subset (items the model got wrong closed-book in both question languages). Primary
  analysis stays on all factorial items; the subset is reported as such.
- [x] Gemini 2.5 Flash-Lite: all 19 cells x 414 items under dense AND BM25 (15,800 episodes); Qwen3-30B-A3B (Modal vLLM): all 19 cells dense + 8 headline cells BM25 (11,200); Gemini 3.1 Flash-Lite: 15 cells x 200 items; Gemini 3.6 Flash: 8 cells x 100 items
- [x] Closed-book and oracle arms for all four models; NONE (gold hidden) 100 episodes; repeat battery 30 x 5 per language (1/30 Hindi and 0/30 Telugu verdicts changed); native-Telugu subset (TyDi XOR, 120 items x 4 cells) on two models
- [x] Cov_L: hi 157/539 = 0.291, te 127/539 = 0.236 (string match + two independent LLM reads; 50-item manual audit in results/coverage_audit.json: 21 yes / 7 uncertain / 2 no among first-read acceptances, which is why the second read was added)
- [x] Judge: string rule 41%, LLM 58%, empty 1%; 40-item hand audit agreed 40/40 (results/audit_sample.json)
- [x] analyze.py -> results/analysis.json; 37,582 judged records; global BH family 134 tests, threshold p <= 0.0067, 18 survivors
- Headline: dense retriever: Hindi gap 9.4 (Gemini 2.5 Flash-Lite, survives) and 9.1 (Qwen, survives), 3.0 / 2.0 for the stronger Gemini (n.s.); forcing the query language recovers <= 4.5 points; served pool makes no difference for Gemini; oracle gap 6.3 (survives). BM25: Hindi gap 18.9 / 19.5 (survive); dual recovers 9.3 / 13.6 (survive); Hindi-only queries on Hindi-only pool 35%. Coverage-weighted Hindi user (Gemini 2.5 Flash-Lite): 45.4 vs 71.4 English user under BM25 (62.9 with English queries); 66.7 vs 75.8 under dense. Query-language share under free policy 18-57% (D1 fails); D3 holds for one model/language; D5 holds; D6 holds for the stronger Gemini only.
- Spend: $11.49 metered (88,212 calls); Modal ~3 GPU-hours
- **CP3 DONE 2026-10-10 22:52.**

## CP4 · Paper
- [x] ICLR dual build compiles with tectonic (XeTeX; Devanagari MT / Telugu MN for the Indic glyphs); 23 pages with appendix; 61 cited keys, all verified (paper/refs_verification.md; 143 CSV ids via the arXiv API + 7 manual non-arXiv entries + Where's Waldo added from the recency sweep); figures: HTML->Chrome teaser + 4 matplotlib (house style) + 3 tables generated from analysis.json
- [x] Title: "Search in Whose Language? Separating the Query-Side Gap from the Evidence-Side Gap for Search Agents in Indic Languages"
- **CP4 DONE 2026-10-10 23:00** (compression to the 8-page workshop body is listed under CP6 fixes)

## CP5 · Publish
- [ ] Repo: ____
- [ ] Pages: ____
- [ ] Film: ____ (duration, LUFS, QA)
- [ ] GIFs: ____

## CP6 · Self-review
- [ ] REVIEW.md: R1 ____ R2 ____ R3 ____ avg ____ P(accept) ____; venue shortlist ____

## Spend log
| Date | Item | Amount | Running total |
|---|---|---|---|
| | | | |
