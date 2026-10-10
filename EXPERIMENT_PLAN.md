# Experiment plan: Search in Whose Language?
Date frozen: 2026-10-10 (CP2). Status: frozen before any grid call. The only model calls made
before freezing were key checks ($0.0002), the LLM coverage pass over Indic articles (stage
`coverage`, ~$0.25) and a 5-episode loop test (archived in `results/pilot/`, $0.002).

## 1. Question

When a user asks an LLM search agent a question in Hindi or Telugu, how much of the accuracy
loss relative to the same question in English comes from the agent's own query behaviour
(query-side gap, QG), how much from the evidence not existing in that language (evidence-side
gap, EG), and how much from reading the evidence (integration gap, IG)? In what language do
agents search when left free, and does forcing the query language recover the loss?

## 2. Pre-registered directions
D1-D6 in `MILESTONES.md`, recorded 2026-10-10 16:10 before any grid call.

## 3. Question bank (`corpus/items.json`, frozen with SHA-256 in `corpus/FROZEN.json`)

| Source | Items | Languages | Parallel en/L | Gold evidence | Role |
|---|---|---|---|---|---|
| IndicGenBench XorQA-In test (2404.16816) | 539 per language, aligned by index | hi, te (en questions from the en file) | yes (human translations) | English gold paragraph given; Indic article located by Wikidata sitelink in the 20261001 snapshot | factorial items where the Indic article contains the answer; coverage population otherwise |
| MLQA hi test (1910.07475) | 130 sampled (seed 11) of 4,918 with shared ids | hi | yes (natively parallel Wikipedia paragraphs) | both gold paragraphs given and injected into the pools | factorial items (evidence in both by construction) |
| TyDi XOR RC te validation (coastalcph/tydi_xor_rc) | 120 sampled (seed 5) of 291 answerable | te only | no (natively written Telugu) | English gold passage | translation-artefact robustness subset (Q=te only) |
| IndicQuest v2 (2608.15535) | not used in the grid | | | | reserved; closed-book India-centric set, no located evidence |

**Factorial eligibility** (`factorial: true`): the Indic article exists in the snapshot and
states the answer, by answer-string match or by LLM verification with the quoted sentence
found in the article (`experiments/coverage_check.py`, stage `coverage`, gemini-2.5-flash-lite).
String-matched items that the LLM pass rejects are dropped. Counts after verification are
written to `MILESTONES.md` CP2.

**Coverage population** for the in-the-wild term: all 539 XorQA items per language.
`Cov_L` = share whose Indic article states the answer (verified as above). A 50-item manual
spot-check (25 per language, stratified over verified-yes / verified-no) ships in
`results/coverage_audit.json`.

## 4. Evidence pools (`corpus/pools/`, `corpus/index/`)

Snapshot `omarkamali/wikipedia-monthly` 20261001. Chunking: paragraphs merged to ~900
characters, title prefixed, at most 12 chunks per article (`build_corpus.py`).

| Pool | Content | Chunks |
|---|---|---|
| hi | all 169,949 Hindi articles | 353,075 (+ injected MLQA hi gold paragraphs) |
| te | all 145,514 Telugu articles | 518,524 |
| en | 129,646 English articles (parquet parts 000-025, ~1.8% of English Wikipedia, random by page id) + the full English article behind every item (`en_extra.jsonl`) + injected English gold paragraphs | ~1.06M + extras |
| hi+en, te+en | unions | |

The English pool is a sample; the Indic pools are complete. The asymmetry is reported, and the
symmetric monolingual check (§7) isolates it.

**Retriever (amended 2026-10-10 after the pilot sanity checks).** Main grid: bge-m3 DENSE retrieval
(1024-d normalised embeddings computed on Modal, exact inner product as an fp16 matmul on the local
GPU, top-5). Second retriever factor: BM25 (bm25s; NFC, lowercase, Unicode word tokens, English
stopwords removed from all documents and queries, no stemming), run on the full core grid for
gemini-2.5-flash-lite and on headline cells for the other models. An equal-weight RRF hybrid was
tried and discarded (gold@5 0.53 vs 0.70 for dense alone on Hindi). Reason for not using BM25 alone: with the question itself as the query, BM25 alone put the
gold chunk in the top-5 for 8% of Hindi and 7% of Telugu items versus 50% of English items
(transliteration spelling variants such as ओरेगन/ऑरेगॉन and Telugu case suffixes defeat exact
token matching); a lexical-only instrument would attribute to the agent what is a retriever
artefact. With bge-m3 the same check gives 0.70 (Hindi query) and 0.68 (English query on the Hindi
pool): dense retrieval is cross-lingual, lexical retrieval is not, so the retriever factor is part of
the query-side gap and is reported as such (D5). Every pool serves `search(query) -> top-5 chunks`.

## 5. Agent

ReAct loop over OpenRouter tool calling (`experiments/agent.py`): system prompt +
`search` tool; at most 3 search steps, then a short final answer in the question's language;
temperature 0; `reasoning.effort = minimal`; max 500 output tokens per step, 200 for the
final answer. Policy sentence is the only prompt difference between cells (`prompts.py`):

| P | Instruction |
|---|---|
| free | none (we log the script of every query) |
| match | query in the question's language |
| english | query in English |
| dual | two queries per step, one in each language |

Logged per search call: query, dominant script (Unicode block, 80% threshold, else Mixed),
hit ids and languages, gold hit (injected gold chunk, located L gold chunk, or any chunk of the
item's en/L article containing a gold answer string).

## 6. Factors and cells

Q in {en, L}; P in {free, match, english, dual}; E in {en, L, both} (served pool).

| Cells | Count |
|---|---|
| Q=L x P{free, match, english, dual} x E{en, L, both} | 12 |
| Q=en x P{free, match} x E{en, L, both} | 6 |
| Q=en x P=dual x E=L | 1 |
| **Core total** | **19** |

Items per language in the core grid: all factorial-eligible items up to 150 per language
(stratified by source; seed 3). Models (OpenRouter; the workspace guardrail allows only
Google models as of 2026-10-10, see MILESTONES):

| Model | Grid | Reason |
|---|---|---|
| google/gemini-2.5-flash-lite | full core + all batteries | cheapest; $0.0002-0.0007 per episode in the pilot |
| google/gemini-3.1-flash-lite | full core | second Gemini generation |
| google/gemini-3.6-flash | headline slice: Q{en,L} x P{free, dual} x E{en, both} (8 cells), 80 items per language | stronger model, 7.5x the price |
| open-weight on Modal (Gemma-4-31B-it or Qwen3-30B-A3B, vLLM) | headline slice if the guardrail stays; full core if the user lifts it and a non-Google family becomes reachable through OpenRouter | second family |

## 7. Controls and batteries

| Battery | Cells | Items |
|---|---|---|
| Closed-book (no tool) | Q{en, L} | all core items |
| Oracle passage | (Q=L, en passage), (Q=en, en passage), (Q=L, L passage where it exists) | all core items |
| Symmetric monolingual | Acc(Q=en, E=en, match) vs Acc(Q=L, E=L, match), BM25 and bge-m3 | core items (cells already in the grid; bge-m3 rerun) |
| NONE (gold hidden) | Q=L, free, pool minus the item's gold | 50 per language |
| Repeat noise floor | Q=L, free, both, 5 identical runs | 30 per language |
| Native Telugu subset | Q=te x P{free, dual} x E{en, both} | 120 TyDi XOR te items |

## 8. Scoring

Alias-aware string rule in both scripts (exact, containment with a 40-character slack, digit
normalisation for Devanagari and Telugu numerals) -> correct. Otherwise an LLM judge
(`google/gemini-2.5-flash`, not in the grid) decides CORRECT/WRONG from the English and
original question, all gold aliases and the candidate; cached per (item, answer). Hand audit:
40 judged items (20 per language, half string-correct, half LLM-decided) in
`results/audit_sample.json`.

## 9. Estimands (`experiments/analyze.py` -> `results/analysis.json`; every paper number)

- Total gap = Acc(Q=en, both, free) - Acc(Q=L, both, free).
- **QG** = the total gap with evidence present in both languages; mediator = share of English
  (Latin-script) search calls under free and gold-hit rate per call. **Recoverable QG** =
  Acc(Q=L, both, dual) - Acc(Q=L, both, free), and the same for english and match.
- **EG (controlled)** = Acc(Q=L, both) - Acc(Q=L, L-only) and Acc(Q=L, both) - Acc(Q=L,
  en-only); the P x E interaction (english vs match, en-only vs L-only).
- **IG** = Acc(Q=en, oracle en) - Acc(Q=L, oracle en); Acc(Q=L, oracle L) reported.
- **In the wild**: Acc_L = Cov_L * Acc(Q=L, both, P) + (1 - Cov_L) * Acc(Q=L, en-only, P) for P
  in {free, dual}, per language and model, with bootstrap CIs on every term; compared with
  Acc(Q=en, en-only, free) as the English user's reference.
- Parametric leakage: closed-book accuracy per cell; attribution = share of correct agent
  answers whose trajectory contained a gold hit.

Statistics: unit = item; paired within-item contrasts; sign-flip permutation (20k) clustered
by source; item-cluster bootstrap 95% CIs (10k); interactions by label permutation (5k);
Benjamini-Hochberg over the full reported family, bold survivors only; the repeat-battery
noise floor beside every headline.

## 10. Budget (cap $30, hard stop $24, shared key; `cost_tracker.py` logs `usage.cost` exactly)

| Item | Episodes | Estimate |
|---|---|---|
| flash-lite 2.5: core 19 cells x ~280 items | ~5,300 x $0.0005 | $2.7 |
| flash-lite 2.5: batteries (closed 560, oracle ~700, none 100, noise 300, native 480) | ~2,100 | $0.8 |
| flash-lite 3.1: core | ~5,300 x $0.0012 | $6.4 |
| gemini-3.6-flash: headline 8 cells x 160 items | ~1,300 x $0.004 | $5.2 |
| LLM judge (gemini-2.5-flash, disagreements only, ~30% of records) | ~4,500 x $0.0002 | $0.9 |
| Coverage LLM pass (done) | 647 | $0.25 |
| Modal open-weight arm (GPU time, not OpenRouter) | 1-2 h L4/A10G | $2-3 (Modal credit) |
| bge-m3 embedding of hi, te and en pools (Modal) | ~2M chunks | $2-4 (Modal credit) |
| Contingency (retries, re-runs) | | $2 |
| **OpenRouter total** | | **~$18** |

If the pilot of the full grid shows per-episode cost above $0.0008 on flash-lite 2.5, cut
items per language to 120 and drop P=match for Q=en before dropping anything else.

## 11. Threats and controls

Parametric leakage (closed-book arm, attribution rate). Translation artefacts (XorQA
questions are human translations; the natively written Telugu subset is the check). Wikipedia
is not the web (said in the abstract; no live arm without a search key). English pool is a
sample (reported; symmetric check). Spelling variation across transliterations breaks lexical
matching (observed in the pilot: question "ओरेगन", article "ऑरेगॉन"); this is part of QG and is
reported as such, with bge-m3 as the retriever that does not depend on it. Judge bias across
scripts (string rule first, audit shipped). Guardrail-limited model families (reported;
open-weight arm on Modal).
