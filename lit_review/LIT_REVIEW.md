# Literature Review: Search in Whose Language?
## Separating the query-side gap from the evidence-side gap for search agents in Indic languages

Date: 2026-10-10. Method: a pre-emption sweep over ~45 phrasings with abstract fetches for every
cited id (`00_preemption_sweep_2026-10-10.md`, 90+ works), an arXiv-API verification pass over all
145 arXiv ids it cites (`verify_refs.py` -> `lit_review.csv`: 143 OK, 2 swapped ids corrected
below, 0 not found), and a recency sweep over 2026-09-15 to 2026-10-10 (`recency_2026-10-10.md`,
~330 titles scanned). Semantic Scholar rate-limited; arXiv direct and HF dataset cards are the basis.

Corrections to the seed sweep: arXiv 2601.05366 is *Lost in Execution: On the Multilingual Robustness
of Tool Calling in LLMs* (Luo et al.) and 2603.05515 is *Enhancing Tool Calling in LLMs with the
International Tool Calling Dataset* (Zhang, Zhu); the sweep had them swapped. 2608.14886 is titled
*Where Does Retrieval Fail? Evaluating RAG Architectures for Agricultural Advisory* (the Bengali
agri-advisory study), 2506.23394 is *Teaching a Language Model to Speak the Language of Tools*
(TUCAN), and ChatRAG-Hi lives inside *Benchmarking Hindi LLMs: A New Suite of Datasets* (2508.19831).

---

## Verdict: ALIVE-BUT-CROWDED

No published work crosses (question language) x (the agent's own search-query language, observed
and then forced) x (the language in which the evidence exists) for an LLM search agent, in any
language. No agentic paper does any two of those three for an Indic language. But the neighbourhood
filled in between June and October 2026, and a reviewer will read a careless version of this paper
as "XBCP with the question language flipped, on Indic". The paper lives on two things nobody has:

1. **The agent's query language as a measured mediator and then a manipulated factor.** We log the
   script of every search call under a free policy and then force the policy (match, English, dual)
   on an evidence pool whose language we control.
2. **A coverage x conditional-accuracy decomposition** of the real-world gap:
   `Acc_L = Cov_L * Acc(L | evidence in L) + (1 - Cov_L) * Acc(L | evidence only in English)`, with
   `Cov_L` measured on the live Indic Wikipedia snapshot and the conditional accuracies from the
   controlled experiment.

A paper whose claim is only "agents do worse on Hindi questions and oracle evidence closes most of
the gap" is dead: XBCP (2606.15345) and MarathiWeb (SIGIR 2026) already say that.

Terminology we avoid because neighbours own it: "retrieval gap" (Liu, Mao, Zhu, Chua 2608.01913),
"query-language preference" (Ki et al. 2610.00606), "exposure" (2609.38670). Ours: **query-side gap
(QG)**, **evidence-side gap (EG)**, **integration gap (IG)**.

---

## Novelty delineation (what is known vs what is ours)

We want to be plain about what is already established. That LLM agents do worse on non-English
tasks is known (MAPS 2505.15935: GAIA 47.4% English vs 35.8% non-English, Hindi included;
OmnilingualGAIA2 2608.08775: Hindi weakest at every size; XBCP; HyperBrowseComp 2610.03574). That
retrievers and generators prefer English and query-language passages is known (Park & Lee
2502.11175; LAURA 2604.20199; Linguistic Nepotism 2509.13930). That the apparent English preference
is partly an artefact of where gold evidence lives is known for single-shot RAG (DELTA 2601.02956's
"gold-availability prior"). That LLMs write tool arguments in the wrong language is known (Lost in
Execution 2601.05366, Hindi included). That parametric Indic knowledge is weaker in Indic scripts is
known (Better To Ask in English? 2504.20022; IndicKLAR 2605.29637; MultiLoKo 2504.10356; Where's
Waldo 2610.00606, Bengali worst). That agent failures split into "never found" vs "found but misused"
is known for English (2608.01913; SearchAuditor 2608.05212; CIVI 2609.08094).

| Closest neighbour | What it established | What it does NOT cover (ours) |
|---|---|---|
| XBCP (2606.15345, Jun 2026) | Deep-research agents on BrowseComp-Plus with the corpus translated into 12 languages; oracle-retrieval decomposition into retrieval vs integration; search-call counts; 64.7% -> 48.8% -> 42.3% original/multilingual/cross-lingual | Question always English; query language never logged or forced; no Indic language; translated rather than native evidence; fixed corpus only |
| MarathiWeb (Kale, SIGIR 2026, DOI 10.1145/3805712.3808534) | Two web-search LLMs on native Marathi local vs translated global queries; failures attributed to "evidence integration rather than missing sources" | One language, two models, live web only; evidence availability observed not manipulated; no query-language manipulation; no parallel English arm; attribution by inspection |
| MAST @ FIRE 2026 Indic track (Thakur et al.; notes due 2026-10-15) | 9 Indic query languages over the English BrowseComp-Plus corpus; organiser baselines 39% EM; participants use LLM query translation | English-only corpus, so the evidence-side gap is zero by construction; a systems shared task, not an attribution study |
| DELTA (2601.02956, ACL 2026 Findings) | Names exposure, gold-availability and cultural priors; regresses them out; English pivot 58.8% vs fused query 62.9% | Single-shot RAG on MKQA; statistical correction, not experimental pool manipulation; no agent, no Indic |
| Where's Waldo (2610.00606, 30 Sep 2026) | ~12K Wikipedia QA pairs in fr/zh/ja/ko/bn where the fact exists only in the source-language article; query language varied with fixed paired context; 12-18 pt preference gaps, Bengali worst | Fixed context, no retrieval, no agent, no search-query language, no coverage decomposition |
| Diagnosing Search Behavior and Failure Modes (2608.01913, Aug 2026) | Every failure = retrieval gap (oracle) vs utilisation gap; 6 agents | English only; the retrieval gap is not split into query formulation vs corpus coverage; no language variable |
| The Cross-Lingual Cost (2507.07543) | Full 2x2 of query language x document language on Arabic/English enterprise data; cross-language ranking is the bottleneck | Two languages, non-agentic; opposite sign to tRAG (2504.03616) on where query translation helps, which our policy x evidence interaction reconciles |
| XRAG (2505.10089, EMNLP 2025 Findings) | The only controlled query-language ablation on a real engine: native vs English-translated Google queries, union best (71.5/68.3/68.9) | Query language set by the authors, not chosen by an agent; no Indic |
| CORAL (2604.25676, ACL 2026 Findings) | An agent that reselects which-language corpus to search; +3.6 pts on low-resource | End accuracy only; no logging of what the agent chose; no decomposition |
| Lost in Execution (2601.05366) | Tool arguments written in the user's language break tools; Chinese, Hindi, Igbo | Generic tools; no search, no evidence pool |

**Ours alone:**
1. Parallel Indic/English questions over a frozen two-language evidence pool in which the language
   of the gold evidence is served or withheld (EN-only / L-only / both), for an iterative search agent.
2. The agent's search-query script logged per call under a free policy (the mediator), then the
   policy forced (match / English / dual) to measure recoverable loss.
3. A coverage term measured on the live Indic Wikipedia snapshot (string match plus LLM
   verification plus manual spot-check) that weights the controlled conditional accuracies into a
   real-world decomposition, per language and model.
4. A natively written Telugu question subset (TyDi XOR) as the translation-artefact check on the
   human-translated parallel set.

---

## Angle A: agentic search in non-English languages

Monolingual non-English browsing benchmarks exist for Chinese (BrowseComp-ZH 2504.19314), Korean
(K-BrowseComp 2606.02404, Ko-WideSearch 2606.27595) and 13 languages with native questions
(HyperBrowseComp 2610.03574, no Indic, best system 31.7%). Cross-lingual agentic evaluation is led
by XBCP (above) and BrowseComp-Plus (2508.06600) as the fixed-corpus paradigm. Multilingual GAIA
variants (MAPS 2505.15935; GAIA-v2-LILT 2604.24929; OmnilingualGAIA2 2608.08775) include Hindi
and consistently find it among the weakest languages, while warning that part of the measured gap
is translation artefact (LILT recovers up to 32.7% by fixing translations). English-only
failure taxonomies (2608.01913; 2608.05212; 2609.08094; 2609.38670) supply the retrieval-vs-use
vocabulary. Logging what agents actually send to search engines is rare: Amani et al.
(2609.19244) do it in English; Sources of Truth (2609.00319) finds non-English queries get fewer
citations. Nobody reports the fraction of search calls an agent issues in English when the user
asks in an Indic language.

## Angle B: multilingual and cross-lingual RAG

Language preference in multilingual RAG is a 2025-2026 thread: retrievers and generators favour
high-resource and query-language passages (2502.11175; 2604.20199; 2605.07249), outputs drift to
English (2511.09984), and reasoning models fail to transfer knowledge across scripts (2603.17070).
DELTA (2601.02956) is the key conceptual precursor: it shows the English preference is confounded
by where gold evidence lives. Pipeline comparisons (tRAG vs MultiRAG vs CrossRAG, 2504.03616;
QTT-RAG 2510.23070; Gupta et al. 2507.22923) disagree on whether translating the query helps, and
The Cross-Lingual Cost (2507.07543) shows the sign depends on the corpus. Attribution matters:
Muller et al. (2305.14332) found up to half of correct XOR-TyDi bn/te answers were not attributable
to any retrieved passage, which is why we run a closed-book arm on every item.

## Angle C: Indic benchmarks and corpora

Parallel questions with known gold location are available from IndicGenBench XorQA-In (2404.16816;
539 test items per language, human-translated from English, English gold passage), MLQA-hi
(1910.07475; natively parallel Wikipedia paragraphs in hi and en), TyDi XOR (2010.11856; natively
written bn/te questions), XQuAD-In (translated passages), and IndicQuest v2 (2608.15535; 3,471
India-centric closed-book items in 20 languages). Retrieval corpora: MIRACL hi/bn/te (2210.09984),
IndicIRSuite (2312.09508), IndicRAGSuite/IndicMSMarco (2506.01615), Hindi-BEIR (2408.09437).
Health-Pariksha (2410.13671) is the closest applied RAG evaluation on Indic queries. Snapshot
sizes on 2026-10-10 (MediaWiki siteinfo): English 7.25M articles, Bengali 192k, Tamil 191k,
Hindi 172k, Telugu 130k; Hindi is 0.2% of Common Crawl pages. Our pool is the
`omarkamali/wikipedia-monthly` 20261001 snapshot (hi 169,949 articles, te 145,514).

## Angle D: knowledge and coverage gaps

Cross-lingual factual recall is frequency- and script-dependent (X-FACTR 2010.06189; mLAMA
2102.00894; Chua et al. 2406.16135; Piratla et al. 2510.15551; 2603.17070). India-centric
questions are answered better in English even by strong models (2504.20022), and code-mixing
narrows the gap (IndicKLAR 2605.29637). ECLeKTic (2502.21228) and Where's Waldo (2610.00606)
construct questions whose evidence exists in only one Wikipedia edition, the closed-book analogue
of our evidence-side manipulation. Wikipedia coverage asymmetry is documented since Hecht & Gergle
(CHI 2010) and WikiGap (2505.24195) shows it runs both ways, which is why our pool keeps local
Indic facts that English lacks.

## Recency (2026-09-15 to 2026-10-10)

One new paper matters: Where's Waldo (2610.00606, 30 Sep) owns the "query-language preference"
and "knowledge gap" vocabulary for a fixed-context setting and includes Bengali; we cite it as the
fixed-context precursor and avoid its terms. Hauck et al. (2610.03136) force the reasoning
language of an agentic RAG system on a German testbed (weak partial overlap). MAST has only
organiser baselines public; working notes are due 2026-10-15 and may describe query-translation
strategies, so this paper should be on arXiv before then or framed against them. Nothing in the
window logs or forces an agent's search-query language in a non-English setting.

## Practical choices justified by the sweep

- Offline frozen pool rather than live web: live engines drift daily and no cheap engine with a
  language filter was keyed; Perplexity Search ($1/1k, language filter) is the optional external
  validity arm if a key appears.
- BM25 primary (bm25s, Unicode tokeniser, no stemming) plus bge-m3 as the second retriever; the
  retriever is a factor because CLIR work shows dense multilingual models retrieve across languages
  where lexical search cannot (2511.19324).
- Coverage via sitelink + answer-string match, then LLM verification, then a manual spot-check,
  because string matching under-counts inflected Indic answers.

References: `lit_review.csv` (145 verified arXiv ids with angle tags); non-arXiv items (MarathiWeb,
MAST, TyDi QA TACL 2020, Hecht & Gergle CHI 2010, WILA-PopQA ACL 2026 KaLLM) are listed in the
sweep with their DOIs or URLs.
