#!/usr/bin/env python3
"""Build docs/index.html (GitHub Pages) from results/analysis.json. CSS is reused from the predecessor site
(templates/site_index_example.html) so the visual system matches paper figures, GIFs and film."""
import json, pathlib, re
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
A = json.load(open(ROOT / "results" / "analysis.json"))
FRO = json.load(open(ROOT / "corpus" / "FROZEN.json"))
SP = json.load(open(ROOT / "results" / "spend.json"))
tpl = (ROOT / "templates" / "site_index_example.html").read_text()
css = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
REPO = "https://github.com/Abraar237/indic-search-gap"
FL = A["models"]["google/gemini-2.5-flash-lite"]
M31 = A["models"].get("google/gemini-3.1-flash-lite", {})
M36 = A["models"].get("google/gemini-3.6-flash", {})
QW = A["models"].get("modal/Qwen3-30B-A3B-Instruct-2507", {})
SURV = set(A["bh_global"]["survivors"])


def c(M, lang, k, f="acc"):
    v = M.get(lang, {}).get("cells", {}).get(k)
    return v[f] if v else float("nan")


def pc(x):
    return f"{100 * x:.0f}"


def pc1(x):
    return f"{100 * x:.1f}"


def con(M, lang, k):
    return M.get(lang, {}).get("contrasts", {}).get(k, {})


def d(M, lang, k, name):
    v = con(M, lang, k)
    if not v or v.get("delta") is None:
        return "n/a"
    s = f"{100 * v['delta']:+.1f} [{100 * v['ci'][0]:+.1f}, {100 * v['ci'][1]:+.1f}]"
    return f"<b>{s}</b>" if f"{name}:{lang}:{k}" in SURV else s


def row(label, M, name):
    return f"<tr><td>{label}</td><td class='n'>{d(M, 'hi', 'total_gap_free_both', name)}</td><td class='n'>{d(M, 'hi', 'QG_recover_dual', name)}</td><td class='n'>{d(M, 'hi', 'EG_both_minus_ENonly', name)}</td><td class='n'>{d(M, 'hi', 'IG_oracle_en', name)}</td><td class='n'>{d(M, 'te', 'total_gap_free_both', name)}</td><td class='n'>{d(M, 'te', 'QG_recover_dual', name)}</td></tr>"


cov_hi = FL["hi"]["coverage"]; cov_te = FL["te"]["coverage"]
dec_hi = FL["hi"]["decomposition_wild"]; decb_hi = FL["hi"]["decomposition_wild_bm25"]
dec_te = FL["te"]["decomposition_wild"]; decb_te = FL["te"]["decomposition_wild_bm25"]
n_calls = SP["n_calls"]
models_rows = row("Gemini 2.5 Flash-Lite (full grid)", FL, "google/gemini-2.5-flash-lite")
if M31: models_rows += row("Gemini 3.1 Flash-Lite (100 items per language)", M31, "google/gemini-3.1-flash-lite")
if M36: models_rows += row("Gemini 3.6 Flash (50 items per language, headline cells)", M36, "google/gemini-3.6-flash")
if QW: models_rows += row("Qwen3-30B-A3B (open weights, full grid)", QW, "modal/Qwen3-30B-A3B-Instruct-2507")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Search in Whose Language?</title>
<meta name="description" content="Separating the query-side gap from the evidence-side gap for search agents in Hindi and Telugu: parallel questions, a frozen two-language Wikipedia pool, the agent's query language logged and then forced, and coverage measured on the live Indic Wikipedias.">
{css}
</head>
<body>
<div class="wrap">
<div class="eyebrow">Search agents · Indic languages · October 2026</div>
<h1>Search in whose language?</h1>
<div class="subtitle">When a search agent answers a Hindi or Telugu question worse than the same question in English, is it the agent's queries or the web? With a cross-lingual search engine the query language barely matters and the remaining gap is the model's reading; with a keyword engine the query language is everything, and most of the evidence an Indian user needs exists only in English.</div>
<div class="byline">Mohammed Abraar · Vizuara Research · abraar@vizz.vizuara.ai</div>
<div class="pills">
  <a class="solid" href="#film">Film</a>
  <a href="paper_iclr_preprint.pdf">Paper (PDF)</a>
  <a href="paper_iclr_submission.pdf">Anonymous build</a>
  <a href="{REPO}">Code + data</a>
</div>

<div class="stats">
  <div class="stat"><span class="v">{FRO['factorial_eligible']['hi:xorqa_in'] + FRO['factorial_eligible']['hi:mlqa']} + {FRO['factorial_eligible']['te:xorqa_in']}</span><span class="k">parallel Hindi + Telugu items</span></div>
  <div class="stat"><span class="v">1.9M</span><span class="k">Wikipedia passages, 3 languages</span></div>
  <div class="stat"><span class="v">19 × 2</span><span class="k">cells × retrievers</span></div>
  <div class="stat"><span class="v">{n_calls:,}</span><span class="k">metered model calls</span></div>
</div>

<div class="toc"><div class="toctitle">Contents</div>
  <a href="#film">0. The film</a>
  <a href="#why">1. Two causes, two fixes</a>
  <a href="#design">2. Same question in two languages, same web served three ways</a>
  <a href="#drift">3. In whose language does the agent search?</a>
  <a href="#gap">4. The gap exists for the cheap models, and forcing the query language does not close it</a>
  <a href="#engine">5. Swap the search engine and the query language becomes everything</a>
  <a href="#coverage">6. Most of the evidence an Indian user needs exists only in English</a>
  <a href="#reading">7. What remains is reading, not the web</a>
  <a href="#prereg">8. Six pre-registered predictions, scored</a>
  <a href="#known">9. What was known, what is new</a>
  <a href="#practice">10. What product teams should do</a>
  <a href="#limits">11. Limitations</a>
  <a href="#repro">12. Reproduce it</a>
</div>

<h2 id="film">0. The film</h2>
<div class="filmwrap"><video controls preload="metadata" poster="assets/film-poster.png" src="assets/film.mp4"></video></div>

<h2 id="why">1. Two causes, two fixes</h2>
<p>Search agents, a language model that writes queries, reads what comes back, and answers, are how hundreds of millions of people in India now reach the web through chat products. When the question is in Hindi or Telugu rather than English, the answer is wrong more often. Two different things can cause that. The agent may write a worse query, or write it in a language where the evidence is not: an English query for a fact only Hindi Wikipedia records, or a Hindi query for a fact only English Wikipedia records. We call that the <b>query-side gap</b>, and prompting or training can fix it. Or the fact may never have been written in the user's language. Hindi Wikipedia has 2.4% of the articles of English Wikipedia, Telugu 1.8%. That is the <b>evidence-side gap</b>, and only cross-lingual search or new content fixes it. A third residue remains when the right passage is in front of the model and it still answers worse in Hindi: the <b>integration gap</b>.</p>
<p>Nobody had separated these for a search agent. The closest study translates an English deep-research corpus into twelve languages with the question always in English and the agent's query language never observed; a Marathi study attributes failures by inspection with one language and no manipulation. We built the instrument that separates them.</p>

<h2 id="design">2. Same question in two languages, same web served three ways</h2>
<div class="fig"><img src="assets/fig1_teaser.png" alt="study design and headline numbers"><div class="figcap">The instrument, the agent's query language, and the decomposition of the real-world gap.</div></div>
<p><b>Parallel questions.</b> Human-translated Hindi/English and Telugu/English pairs from IndicGenBench XorQA-In, and natively parallel Hindi/English Wikipedia paragraphs from MLQA, kept only when the Indic Wikipedia article verifiably states the answer, so that the evidence exists in both languages by construction: {FRO['factorial_eligible']['hi:xorqa_in'] + FRO['factorial_eligible']['hi:mlqa']} Hindi and {FRO['factorial_eligible']['te:xorqa_in']} Telugu items. A natively written Telugu set (TyDi XOR, 120 items) checks that translated questions do not drive the behaviour.</p>
<p><b>A frozen two-language web.</b> The complete Hindi Wikipedia ({FRO['pools']['hi.jsonl']['lines']:,} passages), the complete Telugu Wikipedia ({FRO['pools']['te.jsonl']['lines']:,}) and a 1.8% sample of English Wikipedia plus the full English article behind every item ({FRO['pools']['en.jsonl']['lines'] + FRO['pools']['en_extra.jsonl']['lines']:,}), all from the October 2026 snapshot. The agent has one tool, <span class="num">search(query)</span>, served from the English-only pool, the Indic-only pool, or both.</p>
<p><b>Two retrievers.</b> bge-m3 dense embeddings (cross-lingual: a Hindi query finds English text) and BM25 keyword search (monolingual). With the question itself as the query, the gold passage is in the top five for 70% of Hindi questions under bge-m3 and 8% under BM25, because transliteration variants and Telugu case suffixes defeat exact tokens.</p>
<p><b>The query-language log and lever.</b> A fixed ReAct loop: three searches at most, then a short answer. Under a <b>free</b> policy we log the script of every query; under <b>match</b>, <b>english</b> and <b>dual</b> the agent must query in the question's language, in English, or in both. Closed-book and oracle-passage arms bound the parametric and reading contributions. Four models: Gemini 2.5 Flash-Lite (every cell, both retrievers), Gemini 3.1 Flash-Lite, Gemini 3.6 Flash, and Qwen3-30B-A3B served on our own GPU.</p>

<h2 id="drift">3. In whose language does the agent search?</h2>
<div class="fig"><img src="assets/fig2_query_language.png" alt="share of English queries"><div class="figcap">Share of search queries written in Latin script under the free policy, by question language and served pool.</div></div>
<p>Left free with a Hindi question, Gemini 2.5 Flash-Lite writes <span class="num">{pc(c(FL,'hi','L|free|both','latin_share'))}%</span> of its queries in English, the two stronger Gemini models {pc(c(M31,'hi','L|free|both','latin_share')) if M31 else '–'}% and {pc(c(M36,'hi','L|free|both','latin_share')) if M36 else '–'}%, and Qwen {pc(c(QW,'hi','L|free|both','latin_share')) if QW else '–'}%. With a Telugu question every model searches in English more often: {pc(c(FL,'te','L|free|both','latin_share'))}% for Gemini 2.5 Flash-Lite. The share hardly moves with the pool served: an agent that gets no Hindi text back from an English-only pool does not switch language. The pre-registered prediction of a majority of English queries fails for all but one model on one pool.</p>

<h2 id="gap">4. The gap exists for the cheap models, and forcing the query language does not close it</h2>
<div class="fig"><img src="assets/fig3_policy_by_pool.png" alt="policy by pool"><div class="figcap">Accuracy of the Indic question under four query policies and three served pools (dense retriever); dashed line: the same question in English.</div></div>
<p>With the evidence present in both languages, the Hindi question costs Gemini 2.5 Flash-Lite <span class="num">{pc1(con(FL,'hi','total_gap_free_both')['delta'])}</span> points ({pc1(c(FL,'hi','L|free|both'))} vs {pc1(c(FL,'hi','en|free|both'))}, interval {pc1(con(FL,'hi','total_gap_free_both')['ci'][0])} to {pc1(con(FL,'hi','total_gap_free_both')['ci'][1])}, survives correction) and Qwen3-30B-A3B {pc1(con(QW,'hi','total_gap_free_both')['delta']) if QW else '–'} points. The two stronger Gemini models show no measurable gap ({pc1(con(M31,'hi','total_gap_free_both')['delta']) if M31 else '–'} and {pc1(con(M36,'hi','total_gap_free_both')['delta']) if M36 else '–'} points, intervals through zero). Telugu gaps are smaller and not significant.</p>
<p>Where the gap exists, the lever does little. Matched-language queries: {pc1(con(FL,'hi','QG_recover_match')['delta'])} points. Dual-language queries: {pc1(con(FL,'hi','QG_recover_dual')['delta'])}. English-only queries: {pc1(con(FL,'hi','QG_recover_english')['delta'])}, not surviving correction. The gold passage was already in the top five for {pc(c(FL,'hi','L|free|both','any_gold'))}% of free-policy episodes. The served pool makes no difference either: the Hindi question on the English-only pool scores {pc1(c(FL,'hi','L|free|en'))}, on the Hindi-only pool {pc1(c(FL,'hi','L|free|L'))}, on both {pc1(c(FL,'hi','L|free|both'))}. The one place the policy matters is the pre-registered interaction: English queries beat matched queries by {pc1(con(FL,'hi','english_policy_on_ENonly')['delta'])} points on the English-only pool and lose {pc1(-con(FL,'hi','english_policy_on_Lonly')['delta'])} on the Hindi-only pool (interaction {pc1(FL['hi']['interaction_policy_x_evidence']['delta'])} points, survives), for this model and Hindi only.</p>

<h2 id="engine">5. Swap the search engine and the query language becomes everything</h2>
<div class="gifnote">GIF · the query gap belongs to the engine</div>
<div class="fig"><img src="assets/gifs/engine-not-query.gif" alt="lexical vs cross-lingual search"><div class="figcap">Expected accuracy of a real Hindi user under keyword search (top) and cross-lingual search (bottom), Gemini 2.5 Flash-Lite.</div></div>
<p>The same model and items under BM25: the Hindi question now costs <span class="num">{pc1(con(FL,'hi','total_gap_free_both_bm25')['delta'])}</span> points, the Telugu question {pc1(con(FL,'te','total_gap_free_both_bm25')['delta'])}, and the Indic question with the keyword retriever sits {pc1(-con(FL,'hi','L_free_both_bm25_minus_dense')['delta'])} (Hindi) and {pc1(-con(FL,'te','L_free_both_bm25_minus_dense')['delta'])} (Telugu) points below the same question with the dense retriever. Now the policy matters: dual queries recover {pc1(con(FL,'hi','QG_recover_dual_bm25')['delta'])} of the Hindi points (survives), and English-only queries on the English-only pool reach {pc1(c(FL,'hi','L|english|en|bm25'))} against {pc1(c(FL,'hi','L|free|en|bm25'))} under the free policy. Hindi-only queries on the Hindi-only pool collapse to {pc1(c(FL,'hi','L|match|L|bm25'))}. Under BM25 the agent abstains in {pc(c(FL,'hi','L|free|both|bm25','abstain'))}% of episodes against {pc(c(FL,'hi','L|free|both','abstain'))}% with dense retrieval. The query-side gap is a property of the search engine, not of the user.</p>

<h2 id="coverage">6. Most of the evidence an Indian user needs exists only in English</h2>
<p>For 539 XorQA questions per language we resolved the English source article to its Hindi or Telugu counterpart through Wikidata and checked whether that article states the answer: a string match, then two independent LLM reads of the full article that had to quote a sentence found verbatim, then a 50-item manual audit. The Hindi article exists for {pc1(cov_hi['cov_article'])}% of questions and states the answer for <span class="num">{pc1(cov_hi['cov_verified'])}%</span>; Telugu {pc1(cov_te['cov_article'])}% and <span class="num">{pc1(cov_te['cov_verified'])}%</span>. The audit found the first read too generous (2 of 30 acceptances wrong, 7 uncertain), which is why the second read was added; the figures are conservative.</p>
<div class="fig"><img src="assets/fig4_decomposition.png" alt="decomposition"><div class="figcap">Expected accuracy of a real Indic user: the share of facts the Indic Wikipedia holds times the both-pools accuracy (slate) plus the share only English holds times the English-only accuracy (orange); black is the English user; hatched bars use BM25.</div></div>
<p>Weighting the controlled cells by coverage gives the real-world decomposition. With cross-lingual search the evidence-side term vanishes, because the Hindi query finds the English passage: a Hindi user of Gemini 2.5 Flash-Lite can expect <span class="num">{pc1(dec_hi['free']['acc_wild'])}</span> against {pc1(c(FL,'hi','en|free|en'))} for an English user, and the whole remaining gap is the agent's reading. With keyword search the Hindi user gets <span class="num">{pc1(decb_hi['free']['acc_wild'])}</span> against {pc1(c(FL,'hi','en|free|en|bm25'))}, the Telugu user {pc1(decb_te['free']['acc_wild'])} against {pc1(c(FL,'te','en|free|en|bm25'))}, and most of that loss is the {pc(1 - cov_hi['cov_verified'])}% of facts only English holds; telling the agent to search in English lifts the Hindi user to {pc1(decb_hi['english']['acc_wild'])}.</p>

<h2 id="reading">7. What remains is reading, not the web</h2>
<div class="gifnote">GIF · what remains is reading</div>
<div class="fig"><img src="assets/gifs/reading-not-web.gif" alt="closed-book, search, oracle"><div class="figcap">Hindi questions on Gemini 2.5 Flash-Lite: closed-book, with search, with the gold passage given, and the English question for comparison.</div></div>
<div class="fig"><img src="assets/fig5_retriever_oracle.png" alt="retriever and oracle"><div class="figcap">Closed-book, BM25 search, dense search, oracle passage and the English-question reference, per model and language.</div></div>
<p>With the gold English passage in the prompt, Gemini 2.5 Flash-Lite answers the English question {pc1(c(FL,'hi','en|oracle_en|oracle'))}% of the time and the Hindi question {pc1(c(FL,'hi','L|oracle_en|oracle'))}% (gap {pc1(con(FL,'hi','IG_oracle_en')['delta'])}, survives); given the Hindi passage instead, the Hindi question drops to {pc1(c(FL,'hi','L|oracle_L|oracle'))}%. The cheap model reads English evidence better than Hindi evidence even for a Hindi question. The stronger Gemini models read as well in Hindi as in English (integration gaps of {pc1(con(M31,'hi','IG_oracle_en')['delta']) if M31 else '–'} and {pc1(con(M36,'hi','IG_oracle_en')['delta']) if M36 else '–'} points). Closed-book, the models already know {pc(c(FL,'hi','L|closed|closed'))}% to {pc(c(M36,'hi','L|closed|closed')) if M36 else '–'}% of the Hindi answers, with closed-book gaps of 2 to 4 points; on the pre-specified subset Gemini 2.5 Flash-Lite got wrong closed-book in both languages ({FL['hi']['needs_search_n']} Hindi items) the gap is {pc1(FL['hi']['needs_search_contrasts']['total_gap_free_both']['delta'])} points and dual queries recover {pc1(FL['hi']['needs_search_contrasts']['QG_recover_dual']['delta'])}.</p>

<h2 id="prereg">8. Six pre-registered predictions, scored</h2>
<table>
<tr><th>Direction (recorded before any grid call)</th><th>Result</th></tr>
<tr><td>D1 Agents write a majority of English queries for Indic questions; more for Telugu than Hindi</td><td class="lo">Fails on the majority (30–48%, one exception); holds on Telugu &gt; Hindi for three of four models</td></tr>
<tr><td>D2 A query-side gap exists; dual queries recover at least half; English-only recovers less than dual</td><td>Gap exists for the two cheap models (9 points); dual recovers half for Qwen only; under BM25 dual recovers half for Gemini too; English-only recovers more, not less</td></tr>
<tr><td>D3 English queries help on the English-only pool and hurt on the Indic-only pool</td><td class="hi">Holds for Gemini 2.5 Flash-Lite, Hindi ({pc1(FL['hi']['interaction_policy_x_evidence']['delta'])}-point interaction, survives); absent elsewhere</td></tr>
<tr><td>D4 Coverage below one half, Hindi above Telugu; the coverage term exceeds the agent term for Telugu</td><td>First clause holds ({pc1(cov_hi['cov_verified'])}% vs {pc1(cov_te['cov_verified'])}%); second clause fails under cross-lingual retrieval and holds under BM25</td></tr>
<tr><td>D5 The retriever carries the symmetric monolingual deficit: BM25 &gt; dense &gt; oracle</td><td class="hi">Holds: {pc1(con(FL,'hi','symmetric_monolingual_bm25')['delta'])} &gt; {pc1(con(FL,'hi','symmetric_monolingual')['delta'])} &gt; {pc1(con(FL,'hi','IG_oracle_en')['delta'])} points (Hindi), all survive</td></tr>
<tr><td>D6 With the oracle passage the Indic question is within 5 points of English</td><td>Holds for the two stronger Gemini models; fails by {pc1(con(FL,'hi','IG_oracle_en')['delta'] - 0.05)} points for Gemini 2.5 Flash-Lite</td></tr>
</table>
<p>Noise floor: 30 items re-run five times each at temperature 0 changed the verdict on 1 of 30 Hindi items and 0 of 30 Telugu items.</p>

<table>
<tr><th>Model</th><th>Hindi gap</th><th>Hindi: dual recovers</th><th>Hindi: both − English-only pool</th><th>Hindi: oracle gap</th><th>Telugu gap</th><th>Telugu: dual recovers</th></tr>
{models_rows}
</table>
<p class="figcap">Percentage points with 95% item-bootstrap intervals; bold survives Benjamini–Hochberg over all {A['bh_global']['m']} tests. Positive gap = the English question is answered more often.</p>

<h2 id="known">9. What was known, what is new</h2>
<p>That agents do worse on non-English tasks is known, and Hindi is among the weakest languages in every multilingual GAIA variant. That retrievers prefer English and query-language passages is known, and that the apparent preference is partly an artefact of where gold evidence lives was shown for single-shot RAG. That models write tool arguments in the wrong language is known. What is new is the agent's search-query language as a measured mediator and then a forced factor, parallel Indic/English questions over a pool whose evidence language is served or withheld, the retriever as a factor in the query-side gap, and a coverage term measured on the live Indic Wikipedias that turns the controlled cells into a statement about real users.</p>

<h2 id="practice">10. What product teams should do</h2>
<p><b>Find out which engine you have.</b> With keyword search, translate the Indic query into English before searching; it recovers most of the loss, because most of the evidence is in English. With a cross-lingual dense engine, leave the query alone; the language of the query and of the pool no longer matter. <b>Then look at the model.</b> The residual Indic deficit is reading, not retrieval: the cheapest models answer a Hindi question several points worse with the same passage in front of them, and read Hindi passages worse than English ones; the stronger models do not. <b>Do not expect the agent to adapt.</b> Agents keep searching in the same mix of languages whatever the pool returns.</p>

<h2 id="limits">11. Limitations</h2>
<p>Wikipedia is not the web, and the English pool is a 1.8% sample plus the articles behind the items, so it has fewer near-topic distractors than a real engine returns. Two languages only. The XorQA questions are human translations; the natively written Telugu subset shows the same query-language behaviour but is a different, harder set of items. Coverage was estimated with string matching and two LLM reads with a 50-item audit; the figure is conservative. The closed-model arm is Gemini only because a workspace guardrail blocked other families during the study; the open-weight arm is one model. The judge is a Gemini model; the string rule decides 41% of answers and a 40-item audit agreed on all 40. No live-web arm was run.</p>

<h2 id="repro">12. Reproduce it</h2>
<p>The question bank with coverage flags and hashes, the corpus builder (the snapshot is public), the sitelink resolver, the coverage checks, both retrievers, the agent loop and every prompt, the grid runner, the judge, the single analysis script that produces every number on this page, the audited samples and the spend log are in <a href="{REPO}">the repository</a>. Metered spend: ${SP['total_usd']:.2f} over {n_calls:,} calls, plus about three GPU-hours on a rented A100 for the open-weight arm and the embeddings.</p>
<div class="cite">@article{{abraar2026whoselanguage,
  title={{Search in Whose Language? Separating the Query-Side Gap from the Evidence-Side Gap for Search Agents in Indic Languages}},
  author={{Abraar, Mohammed}},
  year={{2026}},
  note={{Vizuara Research}}
}}</div>

<footer>
Every number on this page traces to <a href="{REPO}/blob/main/results/analysis.json">results/analysis.json</a>, produced by one scripted analysis over the raw call logs. · Mohammed Abraar, Vizuara Research, 2026.
</footer>
</div>
</body>
</html>
"""
(ROOT / "docs" / "index.html").write_text(html)
print("wrote docs/index.html", len(html) // 1024, "KB")
