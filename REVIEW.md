# Simulated A* review: "Search in Whose Language? Separating the Query-Side Gap from the Evidence-Side Gap for Search Agents in Indic Languages"

Target venue: **ICLR** (main-track rubric applied; the paper is pitched at workshop level and a
workshop shortlist is given at the end). Paper type: **analysis / measurement** with a controlled
factorial design. Judged on whether the evidence rules out alternatives and whether the result
changes a practice.

Reviewed build: `paper/iclr/paper_iclr_submission.pdf` (23 pages with appendix; main text through
Limitations ends on page 11; 5 figures, 3 main-text tables, 61 verified references), cross-checked
against `results/analysis.json`, which regenerates from the raw logs.

> Estimated scores from a simulated review, not real reviews. Borderline outcomes at A* venues
> are noisy (about 50% disagreement on borderline papers in the NeurIPS consistency experiments).
> Treat the acceptance number as a base rate.

## Scorecard

| Reviewer | Emphasis | Score (1-10) |
|---|---|---|
| R1 | Rigor | **5** |
| R2 | Novelty | **5** |
| R3 | Clarity / impact | **6** |
| **Average** | | **5.33** (confidence 4/5) |

**Calibrated acceptance estimate, ICLR main track: about 32%.** The 5.0-5.5 band was accepted
31.6% of the time across 5,352 real ICLR submissions in the calibration table (ICLR's overall
rate in the atlas is 27-31%, so no venue adjustment). Half a point more moves the base rate to
48.5%; one point more to 78%. **For a workshop** (multilingual NLP, low-resource languages, or
agents), the same paper sits comfortably in the accept range: workshop acceptance rates run
50-70% and the paper's pre-registration, controls and reproducibility are well above the
workshop norm.

---

## Summary

The paper asks why LLM search agents answer Hindi and Telugu questions worse than the same
questions in English, and separates three causes: the agent's queries (query-side gap), the
absence of evidence in the user's language (evidence-side gap), and reading (integration gap).
It uses human-parallel question pairs whose answer is verifiably in both Wikipedias (287 Hindi,
127 Telugu), a frozen pool of 1.9M Wikipedia passages served English-only, Indic-only or both,
a ReAct agent whose query script is logged under a free policy and then forced (match, English,
dual), and closed-book and oracle-passage arms. Four models run the 19-cell grid under a
cross-lingual dense retriever (bge-m3) and under BM25. Under the dense retriever the cheapest
models lose about 9 points on Hindi, forcing the query language recovers at most a few points,
the served pool makes no difference, and the oracle gap (4-6 points) accounts for most of the
residue; under BM25 the Hindi question costs 19-20 points and dual-language queries recover
9-14. Coverage of the Hindi and Telugu Wikipedias (29% and 24%) is measured and used to weight
the controlled cells into an expected accuracy for a real user. Six directions were
pre-registered; three held, two failed, one split.

## The claim in one sentence

"Whether an Indic user's search-agent deficit is caused by the query language depends on the
search engine: with cross-lingual dense retrieval the query language and the pool language
barely matter and the residue is the model's reading; with lexical retrieval the query language
is the whole story." Easy to restate; a colleague would repeat it.

## What the claim rests on

1. The frozen pool with the gold passage present stands in for the web (assumed, with an
   explicit sample asymmetry; see W1).
2. The both-covered items on which the conditional accuracies are measured are exchangeable
   with the uncovered items the decomposition applies them to (assumed; W2).
3. The string-plus-LLM judge scores Indic and English answers comparably (established by a
   40-item audit with 40/40 agreement, but the audit is small; W6).
4. Prompt-level policy forcing changes only the query language (established: 100% and 1%
   Latin-script shares under the English and match policies, Appendix tables).
5. Temperature-0 nondeterminism is below the effects reported (established: repeat battery,
   1 of 30 and 0 of 30 verdicts changed).

## Strengths

- **The instrument is new and the right one.** Parallel questions, a pool whose evidence
  language is served or withheld, and the agent's query language observed then forced is a
  design none of the eight nearest papers in Table 1 has; the delineation table is honest and
  specific (XBCP never varies the question language, MarathiWeb never manipulates anything).
- **The retriever-dependence finding is the contribution.** The same 287 items and the same
  model give a 9.4-point Hindi gap with bge-m3 and 18.9 with BM25, with the recovery from dual
  queries going from +1.8 (n.s.) to +9.3 (survives); Qwen replicates the pattern (+4.5 to
  +13.6). This reconciles the sign disagreement between query-translation studies
  (Amiraz et al. vs Ranaldi et al.) with a single mechanism.
- **Pre-registration with failures reported.** D1 (majority English queries) fails, the second
  clause of D4 fails under dense retrieval, and the abstract says so.
- **Statistics at a level few agent papers reach.** Paired within-item contrasts, item
  bootstrap, sign-flip permutation, a direct interaction test, one BH family over 134 tests with
  bolding of survivors only, a repeat battery, and a closed-book arm on every item (Muller et
  al.'s attribution concern is answered: 77% of correct agent answers had a gold chunk in the
  trajectory).
- **Coverage is measured, not assumed,** with two independent LLM reads that had to quote a
  verbatim sentence, a manual audit that caught the first read being too generous, and a
  conservative final figure.
- **Cheap and reproducible:** $11.49 metered, every number from one script, hashed corpus,
  verified bibliography, public snapshot.

## Weaknesses (ordered by severity)

1. **The evidence-side "zero" is partly built into the pool. (Serious; fixable.)** Every
   item's gold English paragraph is injected into the English pool, and the full English
   article behind every item is added; bge-m3 then places the gold in the top five for 68-93%
   of question-as-query searches (Section 3.2). In that regime the English-only and both-pool
   cells cannot differ much, so "the evidence-side term vanishes under dense retrieval" is a
   statement about a pool in which the cross-lingual retriever has near-perfect recall of a
   guaranteed-present passage. The web does not guarantee the passage, and a real engine's
   recall at five is far lower. The paper's own BM25 arm shows what happens when recall drops.
   The claim should be stated as conditional on retriever recall, and a recall-degradation
   sweep (e.g., dense retrieval over the full English Wikipedia rather than a 1.8% sample plus
   injected gold, or top-k reduced to 1-2) would turn this from a caveat into a curve.

2. **The decomposition assumes exchangeability it cannot check. (Serious; partly fixable.)**
   Eq. 1 applies conditional accuracies measured on the 29% of items whose Indic article states
   the answer to the 71% whose article does not. Those are different items; the uncovered ones
   are plausibly more local, rarer, and harder. The "expected accuracy of a real user" is
   therefore a lower-bound-free extrapolation. The paper does not run the uncovered items at
   all (it could: they have an English gold passage, so the English-only and both-pool cells
   are defined for them). Running the Indic question on the uncovered items directly would
   replace the extrapolation with a measurement.

3. **"No gap for the stronger models" is not an equivalence result. (Moderate.)** Gemini 3.1
   Flash-Lite (100 items) and 3.6 Flash (50 items) have intervals of $-2$ to $+8$ and $-4$ to
   $+8$ points; a 5-point gap is inside both. The findings list says "the gap belongs to the
   cheap models", which the data support only as "not detected at n=50-100". Either run the
   stronger models on the full item set (about $6 at current prices) or state the detectable
   effect size.

4. **The questions are translations, and the translations are rough. (Moderate; the paper
   admits it.)** XorQA-In questions such as "In which country was the first birth of
   wrestling?" are not what a Hindi user types. The natively written Telugu subset (TyDi XOR)
   shows the same query-language behaviour (44% English) but scores 15 points lower on
   different items, so it checks behaviour, not accuracy. A native Hindi subset is missing
   entirely.

5. **Two languages, one Indic family each, one open-weight model, one closed family.** The
   guardrail explanation for Gemini-only is honest but does not help the reader; the claim
   "the gap belongs to the cheap models" rests on two cheap models and two stronger ones from
   one vendor.

6. **The judge audit is small for a cross-script judge (40 items, 100% agreement).** A
   40/40 result on a stratified sample bounds the error rate at roughly 7% at the 95% level;
   with cells separated by 2-9 points, a judge bias of a few points between scripts would
   matter. 100-150 audited items, with the abstention class checked separately, would settle it.

7. **Closed-book accuracy is high (58-84%), so the agent mostly confirms what the model
   knows.** The pre-specified needs-search subset (97 Hindi items for Gemini 2.5 Flash-Lite)
   gives a 12.5-point gap and a 7.4-point dual recovery, neither surviving. The headline
   contrasts are dominated by items where search is optional; the paper reports this plainly
   but the abstract does not.

8. **Length and venue fit.** The main text runs to page 11 before the appendix; the stated
   target is an 8-page workshop paper. Figures 2-5 are four-panel strips that are hard to
   read at column width. Related work at 1.5 pages can be halved. For ICLR main track the
   contribution is a careful measurement on one benchmark family, which reviewers there tend
   to score 5; the paper is better matched to a multilingual or agents workshop or to ACL
   Findings.

## Format audit (ICLR 2026 norms from the atlas)

- Ablation table: present in spirit (Table 2 lists every paired contrast; the policy and pool
  factors are the ablation). Fine.
- Page-1 teaser: present (Figure 1, HTML-rendered, standard fonts). Fine.
- Error bars / significance: present on every cell and contrast, with BH; well above the
  22-37% base rate. Differentiator.
- Figures 5 and tables 3 in the main text; ICLR accepted papers average more figures; the
  per-model four-panel layout makes each figure dense. Consider one figure per finding with
  the strongest model pair only.
- Topic fit: "LLM representation and generation" and agent evaluation are growing topics at
  ICLR; multilingual evaluation is a minority topic there and a majority topic at ACL venues.

## Questions

1. If the English pool were the full English Wikipedia (7.3M articles) with no injected gold
   paragraph, how far does bge-m3's gold-at-5 fall, and does the evidence-side term reappear?
2. What is the Indic-question accuracy on the uncovered items (evidence only in English),
   measured directly rather than extrapolated?
3. Do the stronger Gemini models show a gap at n=287? What effect size can the n=50 cells
   detect?
4. How much of the BM25 collapse under matched-language queries is transliteration spelling
   variance specifically (a normalised-spelling BM25 would answer this)?
5. Does the judge accept Hindi-script and English answers at the same rate on a larger
   audited sample?

## What would move this to accept (ranked by expected gain per unit effort)

1. **Run the uncovered items directly** (Indic question, English-only and both pools, free
   and dual): replaces the extrapolation in Eq. 1 with a measurement. About 2,000 episodes,
   under $2, half a day.
2. **A retriever-recall sweep**: dense retrieval over the full English Wikipedia (or top-k
   reduced to 1 and 2) to show the evidence-side term as a function of recall. The embedding
   job is the cost (about 7M articles, roughly 20 GPU-hours), the runs are cheap.
3. **Stronger models on the full item set**, so "no gap" becomes an equivalence bound. About
   $6-10, two hours.
4. **A native Hindi question set** (IndicQuest v2 is parallel and India-centric; locate the
   evidence by the same coverage procedure). One day.
5. **Judge audit to 150 items** with a second annotator. Two hours.
6. **Compress to 8 pages**: one figure per finding, Related Work halved, per-cell tables to
   the appendix only. Half a day. With items 1-3 the paper is a 6.0-6.5 at ICLR (78% band);
   with item 6 alone it is ready for a workshop.

## Workshop shortlist

In order of fit: a multilingual / low-resource NLP workshop at ACL or EMNLP (the question
sets, coverage measurement and Indic focus are the natural audience); an LLM-agents or
tool-use workshop at ICLR or NeurIPS (the retriever-dependence of the query-side gap is the
agent-side result); an information-retrieval workshop (SIGIR or ECIR) for the lexical versus
cross-lingual retriever contrast; and the Indic NLP venues (BHASHA, IndoNLP) where the
coverage figures alone are of interest. ACL Findings is a realistic main-venue target after
fixes 1-3.
