# Search in Whose Language?

**Separating the query-side gap from the evidence-side gap for search agents in Indic languages.**

Mohammed Abraar · Vizuara Research · 2026

- **Website:** https://abraar237.github.io/indic-search-gap/
- **Paper:** [`docs/paper_iclr_preprint.pdf`](docs/paper_iclr_preprint.pdf) (named preprint) · [`docs/paper_iclr_submission.pdf`](docs/paper_iclr_submission.pdf) (anonymous build)

When a user asks an LLM search agent a question in Hindi or Telugu, the answer is right less often
than for the same question in English. Two causes produce that drop and need different fixes: the
agent may search badly or in a language where the evidence is not (the **query-side gap**), or the
evidence may not exist in that language at all (the **evidence-side gap**). This study separates them
with parallel questions, a frozen two-language Wikipedia pool whose gold passage is served in English
only, in the Indic language only, or in both, a log of the script of every query the agent writes, and
forced query-language policies. Measured Wikipedia coverage weights the controlled accuracies into a
decomposition of the real-world gap.

## Headline numbers

| | Gemini 2.5 Flash-Lite, Hindi | Qwen3-30B-A3B, Hindi | Gemini 3.1 / 3.6, Hindi |
|---|---|---|---|
| English vs Hindi question, dense search, evidence in both languages | **+9.4** [4.5, 14.3] | **+9.1** | +3.0 / +2.0 (n.s.) |
| recovered by dual-language queries (dense) | +1.8 (n.s.) | +4.5 (p=0.04) | +1.0 / 0.0 |
| both pools minus English-only pool (dense) | -0.7 | +5.6 | −2.0 / 0.0 |
| English vs Hindi question with the gold passage given | **+6.3** | +4.2 | −2.0 / −2.0 |
| English vs Hindi question, BM25 | **+18.9** | **+19.5** | – |
| recovered by dual-language queries (BM25) | **+9.3** | **+13.6** | – |
| share of English queries, free policy | 30% | 18% | 31% / 45% |

Percentage points with 95% item-bootstrap intervals; bold survives Benjamini-Hochberg over all 134 tests. Coverage: the Hindi Wikipedia article states the answer for 29.1% of the 539 XorQA questions, the Telugu one for 23.6%. Coverage-weighted, a Hindi user of Gemini 2.5 Flash-Lite expects 45.4 (BM25) or 66.7 (dense) against 71.4 / 75.8 for an English user; telling the BM25 agent to search in English lifts the Hindi user to 62.9. Measured directly on the 382 uncovered Hindi questions (added after the self-review), the cross-lingual figures are 51.4 against 60.5: the uncovered facts are harder for both users, the gap is unchanged, and Hindi articles that lack the fact distract (serving the Hindi pool costs 5.8 points, survives).

1. **Agents search in a mix of languages and do not adapt** when a pool returns no Indic text.
2. **With a cross-lingual retriever, the query language is not the cause**: forcing it recovers at most a few points and the served pool makes no difference; what remains is the model's reading (4–6 points with the passage given).
3. **With a keyword retriever, the query language is everything**: 19–20 Hindi points lost, half recovered by searching in both languages, because most of the evidence exists only in English.
4. The gap belongs to the cheap models; the stronger Gemini models show none.

Six directions were pre-registered; three held, two failed, one split (see `MILESTONES.md`).

## Reproduce

```bash
pip install -r requirements.txt            # bm25s, datasets, sentence-transformers, torch, pandas, numpy, pymupdf
cp .env.example .env                        # OPENROUTER_API_KEY; Modal token (optional open-weight arm); ELEVENLABS_API_KEY (film only)
cd experiments
python3 build_corpus.py pools hi te en      # downloads wikipedia-monthly 20261001 (hi, te, en parts 000-025) and chunks it
python3 wikidata_sitelinks.py ../corpus/meta/xorqa_en_titles.json
python3 build_items.py                      # XorQA-In, MLQA, TyDi XOR -> corpus/items.json (+ coverage string match)
python3 filter_mlqa.py                      # self-contained MLQA filter (LLM, ~$0.01)
python3 coverage_check.py && python3 coverage_check2.py   # two LLM reads of each Indic article (~$0.85)
python3 fetch_en_articles.py                # English articles behind the items -> pools/en_extra.jsonl
python3 index.py build hi te en hi+en te+en # BM25 (bm25s)
python3 -m modal run modal_embed.py --lang hi   # bge-m3 embeddings on Modal (repeat for te, en), then `modal volume get` into corpus/emb/
bash run_all.sh                             # Gemini grid through OpenRouter (sequential, resume-safe)
python3 -m modal deploy modal_vllm.py && bash run_modal.sh   # Qwen3-30B-A3B open-weight arm
python3 judge.py                            # string rule + LLM judge on disagreements
python3 analyze.py                          # -> results/analysis.json (every paper number)
cd ../figures && python3 build_figures.py && python3 build_gifs.py
cd ../paper/iclr && tectonic paper_iclr_submission.tex && tectonic paper_iclr_preprint.tex
```

Metered spend for the whole study: $11.49 over 88,212 OpenRouter calls (exact per-call `usage.cost` in `results/spend.json`), plus about three GPU-hours on a rented A100 (open-weight arm and bge-m3 embeddings).

## Layout

| path | contents |
|---|---|
| `experiments/` | corpus builder, sitelink resolver, item builder, coverage checks, BM25 + dense + hybrid searchers (`index.py`), agent loop (`agent.py`), grid runner (`indic_runner.py`), judge, `analyze.py`, `prompts.py`, `cost_tracker.py`, Modal scripts |
| `corpus/` | `items.json` (question bank with coverage flags), `FROZEN.json` (hashes), `meta/` (sitelinks, coverage passes); `pools/`, `index/`, `emb/` regenerate and are git-ignored |
| `results/` | raw JSONL per model and retriever, judged labels, `analysis.json`, `coverage_audit.json`, `audit_sample.json`, `spend.json` |
| `figures/` | figure scripts (house style), teaser HTML, GIF builder |
| `paper/iclr/` | LaTeX dual build (anonymous + named), verified references |
| `docs/` | project website (GitHub Pages), both PDFs, film, GIFs |
| `video/` | narration script, film builder |
| `lit_review/` | pre-emption sweep, 145 verified references, novelty delineation, recency sweep |
| `EXPERIMENT_PLAN.md`, `MILESTONES.md` | frozen design, pre-registered directions, checkpoint log |
