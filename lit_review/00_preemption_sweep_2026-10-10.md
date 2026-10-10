# Pre-emption / prior-work sweep
## "Search in Whose Language? Separating the Query Gap from the Evidence Gap for Search Agents in Indic Languages"

Sweep date: 2026-10-10. Method: WebSearch (standard + extended) over ~45 phrasings, WebFetch of arXiv abs/HTML pages (and one PDF text-extraction) for every ID cited, HF dataset cards, official API pricing pages, plus four parallel sub-sweeps (benchmarks; agents + query language; knowledge gaps + corpora; tooling). Every arXiv ID below was verified by fetching its arXiv page unless marked **UNVERIFIED**. Semantic Scholar's API rate-limited (429) and was dropped; arXiv-direct coverage is the basis.

---

## 0. One-paragraph summary

The exact design proposed (parallel questions, Indic question language x agent query language x evidence-pool language, for an iterative LLM search agent, with the agent's own query-language choice logged and then forced) has **not** been published. But the neighbourhood filled in fast during 2026: XBCP (Jun 2026) runs deep-research agents on a BrowseComp-Plus corpus translated into 12 languages with an oracle-retrieval decomposition (English questions only, no Indic); MarathiWeb (SIGIR 2026) evaluates two web-search LLMs on native Marathi local-information queries and attributes failures to "evidence integration rather than missing sources" (one language, no query-language manipulation, no corpus control); the MAST @ FIRE 2026 shared task has an **Indic track** (9 Indic query languages, English BrowseComp-Plus corpus; working notes due 2026-10-15); DELTA (ACL 2026 Findings) names a "gold-availability prior" vs model preference for single-shot mRAG; and two Aug-2026 papers taxonomise search-agent failures into retrieval gap vs utilization gap (English only). Verdict: **ALIVE-BUT-CROWDED**; the paper survives only if it is framed as the *coverage x conditional-accuracy* decomposition with the agent's query language as a measured and then manipulated mediator, on Indic languages, and if it is submitted before MAST participants write it up as a side result.

---

## 1. Multilingual / cross-lingual retrieval and QA benchmarks relevant to Indic languages

Legend: PAR = same questions across languages; EVID = ships a fixed evidence corpus or gold passage.

### 1a. Retrieval benchmarks

| Benchmark | ID / venue | Date | Indic coverage | Format | PAR | EVID | Notes |
|---|---|---|---|---|---|---|---|
| MIRACL (Zhang, Thakur, ..., Lin) | arXiv:2210.09984; TACL 2023 | Oct 2022 | **hi** (1,169 train / 350 dev q), **bn** (1,631 / 411), **te** (3,452 / 828); 18 langs | monolingual passage retrieval over per-language Wikipedia; native queries; graded qrels | No | Yes (`miracl/miracl-corpus`: hi 506k passages / 148k articles, bn 297k / 64k, te 518k / 66k; en 32.9M) | Prebuilt Pyserini BM25 indexes; dev nDCG@10 BM25 hi .458 / bn .508 / te .494 |
| mMARCO (Bonifacio et al.) | arXiv:2108.13897 | Aug 2021 | **hi** only (14 langs) | MS MARCO queries + 8.8M passages machine-translated | Yes (MT) | Yes | MT quality uneven for Hindi |
| IndicIRSuite / INDIC-MARCO (Haq, Sharma, Bhattacharyya) | arXiv:2312.09508; ACL 2024 short | Dec 2023 | 11 Indic (as, bn, gu, hi, kn, ml, mr, or, pa, ta, te) | MS MARCO MT'd into 11 langs + Indic-ColBERT monolingual retrievers | Yes (MT) | Yes | 8.8M passages per language |
| Hindi-BEIR (Acharya, Murthy, Kumar, Sen; IBM) | arXiv:2408.09437 (+2409.05401) | Aug 2024 | **hi** | 15 datasets / 8 tasks, BEIR-style zero-shot; includes a Hindi WikipediaRetrieval subset | Partly | Yes | |
| MLDR / MultiLongDoc (in BGE-M3 paper) | arXiv:2402.03216 | Feb 2024 | **hi** (200 test q; 3,806 long docs) | long-doc retrieval, LLM-generated queries | No | Yes (small) | |
| MMTEB / MTEB(Indic) (Enevoldsen et al.) | arXiv:2502.13595; ICLR 2025 | Feb 2025 | ~25 Indic langs | retrieval tasks = XQuADRetrieval, BelebeleRetrieval | Yes (inherited) | Yes (tiny) | low distractor difficulty |
| IndicRAGSuite / IndicMSMarco (Prasanjith, More, Kunchukuttan, Dabre; AI4Bharat) | arXiv:2506.01615 | Jun 2025 | 13 Indic (as, bn, gu, hi, kn, ml, mr, ne, or, pa, ta, te, ur), ~1,000 q each | 1,000 topic-balanced MS MARCO dev queries + passages, LLM-translated then **human post-edited**; also ~14M synthetic (q, a, reasoning, passage) tuples from 19 Indic Wikipedias (training data) | **Yes** | Yes (translated MS MARCO passages) | Strongest purely-Indic retrieval benchmark; evidence is web passages, not Wikipedia |
| mFollowIR (Weller et al.) | arXiv:2501.19264 | Jan 2025 | none (ru, zh, fa) | instruction-following CLIR | - | - | not useful for Indic |
| NeuCLIR (TREC 2022-24) | arXiv:2304.12367, 2404.08071, 2509.14355 | 2022-25 | none (zh, fa, ru) | CLIR/MLIR with English queries | - | Yes | protocol template only |
| CIRAL (Adeyemi, Oladipo, Zhang, ..., Lin) | SIGIR 2024 resource; FIRE 2023 | 2023-24 | none (ha, so, sw, yo) | English queries vs in-language passages, native judgments | No | Yes | cleanest "query in L1, corpus in L2" template |

### 1b. Open-domain / cross-lingual QA

| Benchmark | ID / venue | Date | Indic | Format | PAR | EVID | Notes |
|---|---|---|---|---|---|---|---|
| TyDi QA (Clark et al.) | TACL 2020 | 2020 | **bn, te** | native info-seeking QA; passage selection / min span / GoldP; Wikipedia 2019-02 | No | Yes (article per q) | |
| XOR-TyDi QA (Asai et al.) | arXiv:2010.11856; NAACL 2021 | Oct 2020 | **bn, te** (7 langs) | TyDi questions unanswerable in-language, answered from **English Wikipedia**; XOR-Retrieve / EnglishSpan / Full | No, but L1 + English answers per q | Yes (en + 7 L1 Wikipedias) | the canonical "evidence only exists in English" set |
| MKQA (Longpre, Lu, Daiber) | arXiv:2007.15207; TACL 2021 | Jul 2020 | **none** (26 langs, verified via HF card) | 10k NQ questions human-translated; language-independent answers | **Yes, fully** | No corpus | the base of almost every mRAG bias paper in sec. 2, hence why none of them has Indic languages |
| MLQA (Lewis et al.) | arXiv:1910.07475; ACL 2020 | Oct 2019 | **hi** (7 langs) | extractive QA; contexts are **naturally parallel Wikipedia paragraphs mined across editions**; G-XLT allows question/context language mismatch | **Yes** | Yes (gold paragraph in each language) | the only set where hi and en gold passages are real parallel Wikipedia text |
| XQuAD (Artetxe, Ruder, Yogatama) | arXiv:1910.11856 | Oct 2019 | **hi** | 1,190 SQuAD QA professionally translated | Yes | Yes (translated en content) | |
| Belebele (Bandarkar et al.) | arXiv:2308.16884; ACL 2024 | Aug 2023 | 15 Indic + romanised hi/bn/ur/ne/si | 4-way MCQ RC over FLORES passages | Yes | Yes (short snippets) | |
| XTREME-UP (Ruder, Clark, Gutkin et al.) | arXiv:2305.11938 | May 2023 | XOR-QA extended to 23 Indic langs (as, bn, gu, kn, ml, mr, or, pa, ta, te, ur, ...) | gold-passage QA w/ negatives; in-language and cross-language retrieval | Yes (within the 23) | Yes (English Wikipedia passages) | |
| AfriQA (Ogundepo et al.) | arXiv:2305.06897 | May 2023 | none (10 African) | XOR recipe for low-resource langs | No | Yes | template |
| MIRAGE-Bench (Thakur, Kazi, Luo, Lin, Ahmad) | arXiv:2410.13716; NAACL 2025 | Oct 2024 | **hi 450, bn 511, te 250** q | mRAG answer-generation arena on MIRACL positives + hard negatives | No | Yes | |
| BordIRlines (Li, Luo, Haider, ..., Callison-Burch) | arXiv:2410.01171; ACL 2025 Findings | Oct 2024 | hi, bn, ur, ne among 49 | 720 territorial-dispute queries x retrieved Wikipedia passages across claimant languages | Yes | Yes | narrow domain; but it *is* "same question, different-language Wikipedia evidence" |
| MLNeedle (Hengle, Bajpai, Dan, Chakraborty; IIT Delhi) | arXiv:2408.10151; NAACL 2025 | Aug 2024 | **hi** (via MLQA) | needle (MLQA gold passage) in mMARCO haystack; needle/haystack language varied | Yes | Yes (synthetic) | a long-context cousin of the proposed design |
| XRAG (Liu, Trenous, Ribeiro, Byrne, Hieber; Amazon) | arXiv:2505.10089; EMNLP 2025 Findings | May 2025 | none (de, es, zh, ar + en) | cross-lingual RAG from recent news | - | Yes | see sec. 4 for its Google query-language experiment |

### 1c. Indic-specific LLM evaluation suites

| Suite | ID / venue | Date | Indic | Format | PAR | EVID |
|---|---|---|---|---|---|---|
| IndicXTREME / IndicQA (Doddapaneni et al.; AI4Bharat) | arXiv:2212.05409; EMNLP 2023 | Dec 2022 | 11 Indic; 18,579 q (13,283 answerable) | SQuAD-v2-style extractive QA over **Indic-Wikipedia paragraphs on Indic-culture topics**; questions written natively per language | No (same topic pool, different questions) | Yes (gold Indic paragraph) |
| IndicGenBench (Singh, Gupta, Bharadwaj, Tewari, Talukdar; Google) | arXiv:2404.16816; ACL 2024 | Apr 2024 | 29 Indic / 13 scripts | CrossSum-In, Flores-In, **XQuAD-In** (12 langs, human-translated passages+questions), **XorQA-In** (28 langs; Indic question, **English** passage, both en and Indic answer spans) | **Yes** | Yes |
| Indic QA Benchmark (Singh, Kumar, Murthy, Sen, Mittal, Ramakrishnan; IBM/IITB) | arXiv:2407.13522; NAACL 2025 Findings | Jul 2024 | 11 Indic | aggregated extractive + abstractive QA (XQuAD, MLQA, IndicQA, XOR-QA, ...), mostly IndicTrans2-translated | Largely yes (MT) | Yes |
| MILU (Verma, Khan, Kumar, Murthy, Sen; AI4Bharat) | arXiv:2411.02538 | Nov 2024 | 10 Indic + en; ~80k exam MCQs | closed-book | partial | No |
| IndicMMLU-Pro | arXiv:2501.15747 | Jan 2025 | 9 Indic | translated MMLU-Pro | Yes | No |
| Pariksha (Watts, Gumma, ..., Sitaram; Microsoft) | arXiv:2406.15053; EMNLP 2024 | Jun 2024 | 10 Indic; 20 native prompts/lang | human + LLM pairwise eval of 30 models | **No** | No |
| L3Cube-IndicQuest v1 / v2 (Rohera et al.; Jain, Mahajan, Joshi, Joshi) | arXiv:2409.08706 (PACLIC 2024); arXiv:2608.15535 | Sep 2024; Aug 2026 | en + 19 Indic; v2: 3,471 India-centric QA x 20 langs = 69,420 | closed-book factual QA | **Yes, fully** | No corpus (but India-centric, so Indic-Wikipedia coverage plausible) |
| IndicSQuAD (Endait et al.; L3Cube) | arXiv:2505.03688; PACLIC 2025 | May 2025 | 9 Indic (exact list UNVERIFIED) | SQuAD translated with span alignment | Yes | Yes (translated en paragraphs) |
| Global-MMLU (Singh, Romanou, Fourrier, Adelani et al.) | arXiv:2412.03304 | Dec 2024 | bn, hi, te, ne, si | translated MMLU + culturally-sensitive tags | Yes | No |
| INCLUDE | arXiv:2411.19799; ICLR 2025 | Nov 2024 | bn, hi, ml, ne, ta, te, ur | native regional exams | No | No |
| MultiLoKo (Hupkes & Bogoychev; Meta) | arXiv:2504.10356 | Apr 2025 | **hi, bn, ta, te, mr, ur** among 31 | 500 **locally-sourced** questions per language (from most-visited Wikipedia pages) + human/MT translations to and from English | Yes (translated partitions) | No corpus, but questions are anchored to Wikipedia pages |
| ECLeKTic (Goldman, Shaham, Malkin et al.; Google) | arXiv:2502.21228 | Feb 2025 | **hi** among 12 (per Google blog; abs page does not list) | closed-book QA from Wikipedia articles that exist in **only one** language edition | translated | No corpus, but by construction evidence exists only in one language |
| BharatBench (Krutrim) | tech report, no arXiv (Krutrim-2 paper arXiv:2502.09642 references it) | Feb 2025 | 8 Indic | multimodal leaderboard | UNVERIFIED | No |
| Health-Pariksha (Gumma, Raghunath, Jain, Sitaram) | arXiv:2410.13671 | Oct 2024 (rev. Dec 2025) | Indian English + 4 Indic; 750 real health-chatbot queries | 24 LLMs under one fixed RAG pipeline | No | fixed pipeline | factual correctness lower for Indic queries; Indic-tuned models not reliably better |
| Others (no retrieval): BhashaBench V1 arXiv:2510.25409; ParamBench arXiv:2508.16185; IndicParam arXiv:2512.00333 (EMNLP 2026); IndicIFEval arXiv:2602.22125; BHRAM-IL arXiv:2512.01852; IndicKLAR arXiv:2605.29637 (EMNLP 2026 Findings; 18 Indian langs + 11 code-mixed pairs, parallel facts); Updesh arXiv:2509.21294 (training data); Sangraha / IndicLLMSuite arXiv:2403.06350 (pretraining corpus). | | | | | | |

### 1d. 2025-2026 Indic RAG / retrieval benchmarks (beyond IndicMSMarco)

| Resource | ID | Date | Notes |
|---|---|---|---|
| ChatRAG-Hi (Kamath et al.; NVIDIA) | arXiv:2508.19831; BHASHA 2025 | Aug 2025 | Hindi conversational RAG, 5,948 items parallel to ChatRAG-Bench; gold context per turn |
| AgriTrust-RAG (Reza, Maria, Nimi) | arXiv:2608.14886 | Aug 2026 | Bengali agri-advisory; 1,000 queries (native / colloquial / English) over 2,882 nodes; BM25 R@10 collapses .506 -> .004 for English queries over the Bengali corpus; a small, domain-specific instance of the query-language x corpus-language effect |
| Tulu legal RAG (Shetty, Setty, Vidra) | arXiv:2608.28645 | Aug 2026 | Tulu queries over Kannada documents; "fact substitution" / "confabulation" failure modes |
| Persona-instruction retrieval, 12 Indian langs (Shah, Beniwal, Singh; IITGN) | arXiv:2601.10205 | Jan 2026 | cross-lingual retrieval, not factual QA |
| MEMERAG (Cruz Blandón et al.; Amazon) | arXiv:2502.17163; ACL 2025 | Feb 2025 | meta-evaluation of RAG judges on MIRACL native questions; language list not confirmed |
| M4-RAG | arXiv:2512.05959; CVPR 2026 | Dec 2025 | multimodal, 42 langs; Indic membership UNVERIFIED |

Searched but **not found as real artefacts**: "IndicRAG" (GitHub project only), "Bharat RAG benchmark", standalone "IndicBEIR"/"IndicMTEB" papers (MTEB(Indic) inside MMTEB is the real thing), any Sarvam text-retrieval benchmark, any Hindi/Tamil BrowseComp.

**Parallel Indic/English question sets usable for a factorial design:** MLQA (hi), XQuAD / XQuAD-In, XorQA-In (28 Indic, English passage), Belebele, IndicMSMarco (13), IndicQuest v1/v2 (19), MultiLoKo (hi, bn, ta, te, mr, ur; local + translated partitions), BordIRlines, ChatRAG-Hi, MLNeedle, Global-MMLU (bn/hi/te). **Fixed evidence corpora:** MIRACL (hi/bn/te Wikipedia), XOR-TyDi (en + L1 Wikipedias), TyDi QA, IndicMSMarco, IndicQA (gold Indic paragraphs), MLQA (parallel gold paragraphs).

**Best bases:** (1) **MLQA-hi**: the only set where Hindi and English gold passages are genuinely parallel Wikipedia paragraphs, so the same fact can be planted in the en pool, the hi pool, or both (~5k items, Hindi only). (2) **IndicGenBench XorQA-In + XQuAD-In**: human-translated parallel questions in 28 / 12 Indic languages with a pinned English Wikipedia passage; because XorQA-In originates from bn/te TyDi askers, topics skew South-Asian and Indic-Wikipedia counterparts are findable via Wikidata sitelinks. (3) **MultiLoKo local partitions (hi/bn/ta/te/mr) + IndicQuest v2** for India-centric *local-knowledge* questions whose natural evidence language is Indic; pair with MIRACL hi/bn/te corpora (full Wikipedia, graded qrels, prebuilt indexes) for realistic distractors.

## 2. Multilingual RAG analysis papers (language preference, pivoting, query vs document language)

All arXiv IDs below were verified by fetching the arXiv abstract page on 2026-10-10 unless marked otherwise.

| # | Paper | ID / venue | Date | Languages (Indic?) | What it does |
|---|---|---|---|---|---|
| 2.1 | Park & Lee, *Investigating Language Preference of Multilingual RAG Systems* | arXiv:2502.11175; ACL 2025 Findings | Feb 2025 (v4 Jun 2025) | MKQA subset: en, ko, zh, fr, ja, it, pt, es. **No Indic.** | Defines MultiLingualRankShift (MLRS): translate non-query-language passages into the query language, re-rank, measure rank shift. Finds retrievers prefer high-resource and query-language passages; generators prefer query-language / Latin-script passages. Proposes DKM-RAG (fuse translated passages + parametric knowledge). Reports that for low-resource MKQA/Global-MMLU languages only out-of-language gold passages exist for most queries (e.g. 88% Khmer, 91% Yoruba) -- i.e. an evidence gap, stated but not isolated experimentally. |
| 2.2 | Park, Kim, Hwang & Lee, *Enhancing Multilingual RAG Systems with Debiased Language Preference-Guided Query Fusion* (DeLP / DELTA) | arXiv:2601.02956; ACL 2026 Findings | Jan 2026 | MKQA 2.7K (KILT-NQ overlap): en, ar, es, zh, ja, de, ko, th. **No Indic.** | Argues the apparent "English preference" of mRAG is an artefact of three structural priors: exposure prior (English corpus dominance), gold-availability prior (gold evidence concentrated in English Wikipedia), cultural prior. Regresses them out (DeLP); residual shows retrievers favour *monolingual* query-document alignment. English pivoting (translate query to English) is a strong baseline (58.8%) that DELTA (fused English + local query) beats (62.9%). **This is the closest existing statement of "evidence gap vs. model behaviour" -- but at the level of a single-shot retriever, not an agent, and without Indic languages.** |
| 2.3 | Wang et al., *All Languages Matter: Understanding and Mitigating Language Bias in Multilingual RAG* (LAURA) | arXiv:2604.20199; ACL 2026 main | Apr 2026 | MKQA 13 langs: ar, de, en, es, fi, fr, it, ja, ko, pt, ru, th, zh. **No Indic.** | Shows rerankers favour English and the query language ("diagonal + horizontal" bias; ~60% of top docs are English or query-language). Estimated-oracle analysis (best top-5 per language group) shows a 12.9-20 pt 3-gram-recall gap vs vanilla reranking. LAURA aligns the reranker with downstream generative utility. |
| 2.4 | Wu et al., *Not All Languages are Equal: Insights into Multilingual RAG* (Futurepedia) | arXiv:2410.21970 | Oct 2024 | en, fr, es, pt, zh, ja, ko, ar. **No Indic.** | Builds a fully parallel, future-dated (2124-2200) Wikidata-derived benchmark to remove parametric leakage. Three settings: monolingual extraction, cross-lingual transfer, multilingual selection. English benefits from RALM selection bias; Arabic lags badly (32.7 vs 72.8 recall for GPT-3.5). Good template for *parallel* questions with controlled evidence. |
| 2.5 | Li et al., *Multilingual RAG for Culturally-Sensitive Tasks* (BordIRlines) | arXiv:2410.01171; ACL 2025 Findings | Oct 2024 (v2 Jun 2025) | 49 languages (territorial disputes; includes some Indic claimant languages via Wikipedia but not analysed as such) | Compares in-language vs cross-lingual vs multilingual retrieval for geopolitical questions; multilingual retrieval improves consistency and lowers bias; low-resource query languages show wide citation variance. |
| 2.6 | Ranaldi, Haddow & Birch, *Multilingual RAG for Knowledge-Intensive Task* (tRAG / MultiRAG / CrossRAG) | arXiv:2504.03616; EACL 2026 Findings | Apr 2025 | Not Indic-focused (MKQA/XOR-TyDi style; see paper) | Explicitly compares translate-query-then-retrieve-English (tRAG), direct multilingual retrieval (MultiRAG), and retrieve-then-translate-documents (CrossRAG). tRAG "suffers from limited coverage", MultiRAG from inconsistency; CrossRAG wins. **This is the canonical "query translation vs direct retrieval" comparison for RAG (non-agentic).** |
| 2.7 | Qi, Fernández & Bisazza, *On the Consistency of Multilingual Context Utilization in RAG* | arXiv:2504.00597; MRL 2025 @ EMNLP (best paper) | Apr 2025 | 48 languages across 3 QA datasets (XOR-TyDi => includes bn, te) | LLMs extract answers from cross-lingual passages well but struggle to answer in the right language; query-language distractors hurt slightly more than other-language ones. Isolates the *generation* side given gold passages. |
| 2.8 | Liu et al. (Amazon AGI), *XRAG: Cross-lingual Retrieval-Augmented Generation* | arXiv:2505.10089; EMNLP 2025 Findings | May 2025 | news-based; see paper for language list (no Indic reported) | Benchmark where the user language mismatches retrieved documents; finds response-language correctness failures in monolingual retrieval and cross-lingual reasoning failures in multilingual retrieval. |
| 2.9 | Amiraz et al., *The Cross-Lingual Cost: Retrieval Biases in RAG over Arabic-English Corpora* | arXiv:2507.07543 | Jul 2025 | ar, en (corporate corpora) | **Full 2x2 of query language x document language** with documents drawn uniformly. Finds the retriever's cross-language ranking is the bottleneck (Hits@20 drops 30-50 pts cross-lingually); fixes: enforce equal retrieval from both languages, or translate the query. Non-agentic, two languages, private corpora. |
| 2.10 | Moon, Kim & Verma, *Quality-Aware Translation Tagging in Multilingual RAG* (QTT-RAG) | arXiv:2510.23070; MRL 2025 | Oct 2025 | ko, fi, zh on XOR-QA / MKQA | Tags translated documents with quality scores before generation; beats CrossRAG and DKM-RAG. |
| 2.11 | Li, Xu & Xie, *Language Drift in Multilingual RAG* (SCD) | arXiv:2511.09984; AAAI 2026 oral | Nov 2025 | typologically diverse; not Indic-specific | Characterises output-language drift toward English when evidence language mismatches; decoding-time fix. |
| 2.12 | Lee, Song & Kang, *CORAL: Adaptive Retrieval Loop for Culturally-Aligned Multilingual RAG* | arXiv:2604.25676; ACL 2026 Findings | Apr 2026 | cultural QA benchmarks; not Indic-specific | Agentic loop that reselects *which corpus* (language) to search and rewrites the query when evidence is insufficient; +3.6 pts on low-resource languages. **Closest "agent decides the search language" method paper**, but evaluates end accuracy only, no gap decomposition. |
| 2.13 | Gupta et al., *How and Where to Translate? Translation Strategies in Cross-lingual LLM Prompting* | arXiv:2507.22923 | Jul 2025 | low-resource focus; classification tasks with English KB | Pre-translation vs cross-lingual prompting when the KB is English-only. |
| 2.14 | Goworek, Macmillan-Scott & Özyiğit, *Bridging Language Gaps: Advances in CLIR with Multilingual LLMs* (survey) | arXiv:2510.00908 | Oct 2025 | survey | Survey of CLIR: translation-based -> embedding-based -> generative; no agent coverage. |
| 2.15 | Goworek et al., *What Drives Cross-lingual Ranking?* | arXiv:2511.19324 | Nov 2025 | three CLIR benchmarks, cross-script pairs | Document translation gives minimal benefit to CLIR-trained dense retrievers; gains concentrate in low-resource and cross-script pairs. |
| 2.16 | Asenov et al., *Retrieval or Representation? Reassessing Benchmark Gaps in Multilingual and Visually Rich RAG* | arXiv:2603.04238; ICLR 2026 workshop | Mar 2026 | multilingual document RAG | Decomposes benchmark gains into transcription/representation vs retriever; argues for decomposed evaluation. Methodologically kin to the proposed paper. |
| 2.17 | Wu, Ren & Verberne, *What are the limits of cross-lingual dense passage retrieval for low-resource languages?* | arXiv:2408.11942 | Aug 2024 | am, km on MKQA/AmQA | mDPR fails on extremely low-resource languages; alignment training gives modest gains. |
| 2.18 | Muller et al., *Evaluating and Modeling Attribution for Cross-Lingual QA* | arXiv:2305.14332; EMNLP 2023 | 2023 | XOR-TyDi: **bn, te**, fi, ja, ru | Up to ~50% of exact-match answers are not attributable to any retrieved passage -> parametric memory confounds "retrieval success". Important control for the proposed design. |
| 2.19 | Li, Fan & Zhuang, *Where Privacy Risk Lives in English-Source Multilingual RAG: A Stage-Decomposed Audit Across Five Query Languages* | arXiv:2608.05163 | May 2026 | en, ar, sw + 2 | Stage-decomposed audit with query back-translation ablation (privacy, not accuracy). Shows the "stage decomposition" framing is in the air. |
| 2.20 | Sumyk & Kosovan, *Toward Agentic RAG for Ukrainian* | arXiv:2604.14896; UNLP 2026 shared task | Apr 2026 | uk | Agentic RAG with rephrase/retry loops; retrieval is the bottleneck. Small-scale analogue in one non-English language. |

Additional mRAG-bias entries verified by the sub-sweeps: **Linguistic Nepotism** (Ki, Carpuat, McNamee, Khashabi, Yang, Lawrie, Duh; arXiv:2509.13930; ICML 2026 spotlight) -- models preferentially cite English sources even over more relevant non-English ones, worse for low-resource languages; **Faux Polyglot** (Sharma, Murray, Xiao; arXiv:2407.05502; NAACL 2025) -- in cross-language RAG LLMs prefer query-language documents and fall back to high-resource languages when little exists; **Chirkova et al., RAG in multilingual settings** (arXiv:2407.01463; 2024) -- 13-language baseline, notes named-entity spelling across scripts breaks matching; **MLAIRE** (Jang et al.; arXiv:2605.07249; May 2026) -- Language Preference Rate / Lang-nDCG metrics over 31 retrievers using parallel passages; **Macmillan-Scott, Goworek, Özyiğit, Generative Query Expansion for CLIR** (arXiv:2511.19325) -- LLM query expansion helps least across scripts; **LangSAE Editing** (Kim et al.; arXiv:2601.04768) -- removes language-identity directions in embeddings, largest gains for script-distinct languages; **LcRL** (Qi et al.; arXiv:2601.14896) and **CroSearch-R1** (Qi et al.; arXiv:2604.25182; SIGIR 2026 short) -- Search-R1-style RL that treats query/evidence language as a training variable (no Indic reported); **TR-RAG** (arXiv:2607.02966; Jul 2026; English-evidence cross-lingual RAG on MKQA, no Indic); **XHotpotQA** (Barati et al.; arXiv:2608.27481; Aug 2026; 10-24 pt drops when question and evidence differ in language/script).

---

## 3. Search AGENTS (not just RAG) in non-English / low-resource languages

### 3a. Monolingual non-English browsing benchmarks

| Paper | ID / venue | Date | What it does | Gap-decomposition? |
|---|---|---|---|---|
| BrowseComp-ZH (Zhou et al., 16 authors) | arXiv:2504.19314 | Apr 2025 | 289 reverse-engineered Chinese-web questions; >20 systems, most <10%, OpenAI Deep Research 42.9% | No; no query-language analysis |
| K-BrowseComp (Lee et al.) | arXiv:2606.02404 | Jun 2026 | 400 Korean-context problems; frontier 30-46%, Korean domestic LLMs 0-10%; failure taxonomy ("sparse entity normalization failure", "search-result selection failure") | taxonomy, but not query-language vs evidence |
| Ko-WideSearch (Jeong) | arXiv:2606.27595 | Jun 2026 | Korean breadth-search; 20 agents | No |
| WideSearch (Wong et al.) | arXiv:2508.07999; ICLR 2026 | Aug 2025 | 100 EN + 100 ZH broad-collection tasks | language not treated as a variable |
| WebWalkerQA (Wu et al.) | arXiv:2501.07572; ACL 2025 | Jan 2025 | 680 EN/ZH traversal QA | No |
| xbench-DeepSearch (Chinese) | GitHub `xbench-evals`; **UNVERIFIED as an arXiv paper** | 2025 | 100 evergreen Chinese deep-search questions | No |
| Tongyi DeepResearch tech report | arXiv:2510.24701 | Oct 2025 | 30B-A3B open agent; reports BrowseComp-ZH, WebWalkerQA, xbench | No |
| HyperBrowseComp (Aji et al., 17 authors) | arXiv:2610.03574 | **Oct 2026** | 423 natively authored questions in 13 languages (en, zh, de, id, th, vi, ko, fr, es, pt, ja, ar + 1; **no Indic**); multimodal; best Gemini 3.7 Flash 31.7% | per-language differences attributed to "intrinsic question difficulty"; no parallel versions; no query-language analysis |

### 3b. Cross-lingual / multilingual agentic benchmarks and analyses

| Paper | ID / venue | Date | What it does | What it does NOT do |
|---|---|---|---|---|
| **XBCP -- Cross-Lingual BrowseComp-Plus** (Lu, Zeng, Qi, Yu, Zhao, Yang, Yanaka, Yokoya, Xuan) | arXiv:2606.15345 | Jun 2026 | English BrowseComp-Plus questions; evidence corpus translated into 12 langs (zh, en, fr, de, ja, ko, pt, es, sw, wo, yo, zu); two regimes (cross-lingual: one language per query; multilingual: corpus split across 12). 4 agents (GPT-OSS-20B/120B, Qwen3.6-35B-A3B, DeepSeek-V4-Pro) x 5 retrievers (BM25, Qwen3-Emb-4B/8B, mE5-large, Arctic-Embed-L-2.0). Metrics: accuracy, evidence recall, search calls, calibration, citation fidelity, **oracle retrieval**. DeepSeek-V4-Pro + Qwen3-Emb-8B: 64.7% original -> 48.8% multilingual -> 42.3% cross-lingual; oracle 65.7%; retrieval/search gap 55-75 pp; evidence recall 72.8 -> 53.8. Per-language tool accuracy (Table 5, Qwen3.6-35B + Qwen3-Emb-8B): Swahili 17.4, Wolof 14.5, Yoruba 7.3, Zulu 4.4. Also: concatenating the agent's reasoning trace to the query (+3.3 acc, +4.9 recall) and the sentence "cross-lingual deep research should treat query formulation as part of the retrieval problem". | User question always English; no logging or forcing of query language; no Indic; translated not native evidence; fixed corpus only; decomposition is retrieval-vs-integration, not query-side vs corpus-side; limitations list only single-seed runs and untuned hyperparameters |
| BrowseComp-Plus (Chen, Ma, Zhuang, ..., Lin) | arXiv:2508.06600; NeurIPS 2025 D&B | Aug 2025 | fixed ~100k-doc corpus with human-verified positives and mined negatives; retriever-swappable | English only; infrastructure |
| **MAST @ FIRE 2026 -- Multilingual Agentic Search Track** (Thakur, Zhang, Sharifymoghaddam, Ma, Chen, Lin; Waterloo) | mast-benchmark.github.io; overview paper not yet out | test data Aug 1 2026; runs Sep 25 2026; working notes **Oct 15 2026** | Track 1: 15 languages incl. hi, bn, ur, ta. **Track 2 (MAST Indic): hi, bn, te, ta, gu, kn, pa, ml, or (9 scripts)**; 50 queries/language, 1,050 QA pairs total; corpus = ~100k **English** BrowseComp-Plus docs; "queries are asked in one language, documents & answers are in English, and systems can reason, iteratively search, plan, and synthesize in either language"; metrics Recall + EM; "direct translation of the original query to English as the only retrieval strategy is discouraged" | English-only corpus => cannot measure an evidence gap; shared-task format (systems, not analysis); participants' notes will likely report query-translation strategies -- the main crowding risk |
| **MarathiWeb -- Local Information Access in Marathi: Evaluating LLM-Native Web Retrieval in a Low-Resource Environment** (Kale) | SIGIR 2026, DOI 10.1145/3805712.3808534 (researchr "Kale26"); no arXiv found; ACM page 403 | Jul 2026 | separates translated global queries from natively authored local Marathi information needs; two frontier LLMs with built-in web search vs a Google baseline; "despite high tool invocation rates, accuracy drops sharply in Marathi, most severely for local queries, with the dominant failures arising from evidence integration rather than missing sources"; one web call beats multi-step search | one language, two models, live web only (no corpus control), no query-language manipulation, no parallel English arm reported in abstract; author list from researchr only |
| MAPS (Hofman, Brokman, ..., Marchisio, Goldfarb-Tarrant, Vainshtein) | arXiv:2505.15935; EACL 2026 Findings | May 2025 | GAIA/SWE-bench/MATH/ASB translated into 11 langs incl. **Hindi**; GAIA 47.4% en vs 35.8% mean non-en; OpenDeepResearch "displays a clear English bias: its planning steps align more closely with task instructions in 85% of cases" | plan-level, not query-level; MT'd tasks |
| GAIA-v2-LILT (Kim, Uhlig, Wuebker) | arXiv:2604.24929 | Apr 2026 | re-audits MAPS-style MT for ar, de, **hi**, ko, pt; proper adaptation raises success up to 32.7% over minimal MT | warns that much of the measured Hindi agent gap is translation artefact |
| OmnilingualGAIA2 (Caciolai, ..., Ruder, Costa-jussà; Meta) | arXiv:2608.08775 | Aug 2026 | GAIA2 in 10 langs incl. **Hindi**; universal gap 8.8-18.4 pass@3; attribution: 55.4% agent failures, 34.5% translation defects, 10.1% verifier; "hin and jpn are the weakest languages at every size" (Qwen eng 31.6 vs hin 9.2 pass@1); off-English agents spend more tool budget on exploratory reads | not search; no query-language stats |
| Pahuja et al., Actionable Diagnosis of Multilingual Multi-Agent Planning Failures (TART) | arXiv:2608.03735 | Aug 2026 | information lost at the plan -> tool-argument interface, worse for low-resource langs; +5.6 on multilingual GAIA | not search-specific |
| BabelArena (Kuang et al.; Alibaba) | arXiv:2609.23490 | Sep 2026 | 16k instances, 23 langs; low-resource langs show more tool-use errors, ~2x tokens | Indic coverage UNVERIFIED |
| PolyWorkBench (Li et al.) | arXiv:2607.06008 | Jul 2026 | cross-lingual long-horizon tool workflows | not web search |
| Search Arena (Miroyan et al.; LMArena) | arXiv:2506.05334 | Jun 2025 | 24k battles, 70+ languages (en 58%, ru 12%, zh 7%) | no per-language analysis; a source of real Indic prompts |
| Characterizing Web Search by Conversational LLM Agents (Amani, ..., Gummadi, Ravichander, Zafar, Das; MPI-SWS) | arXiv:2609.19244 | Sep 2026 | in-vivo + in-vitro study of ChatGPT/Claude/Grok/DeepSeek search decisions and query rewriting | "primarily focuses on English-language interactions"; its query-logging method is exactly what an Indic audit needs |
| Sources of Truth (Nguyen et al.) | arXiv:2609.00319 | Aug 2026 | 15k citations across ChatGPT/Perplexity/Google AIO in en + 6 langs; non-English queries get fewer citations and are routed to language-appropriate sources less often | languages not enumerated |
| Query language selects the market (Żatuchin) | arXiv:2608.30052 | Aug 2026 | 234 tests: question language (not exit IP) determines which market a generative search interface recommends | single-author audit |
| Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents (Liu, Mao, Zhu, Chua) | arXiv:2608.01913 | Aug 2026 | every failure sorted into **retrieval gap** (evidence never found; oracle evidence) vs **utilization gap** (found, misused); 6 agents on BrowseComp(-Plus) | English only; no split of retrieval gap into query vs corpus |
| SearchAuditor (Liang et al.) | arXiv:2608.05212 | Aug 2026 | 1,243 failed trajectories, 8 models; search-specific root causes; search snippet reports "Search Coverage Gap" only 22.8% of failures | English only |
| CIVI / ARISE (Liu, Zhong, Zhang, Li) | arXiv:2609.08094 | Sep 2026 | source-injection ablation; 72.1% of civic-info failures retrieval-bound vs parametric | English only |
| DeepResearchGym (Coelho et al.; CMU) | arXiv:2505.19253 | May 2025 | reproducible search API over ClueWeb22/FineWeb | English only; infra |
| Code-Switching IR (Zeng, Lu et al.; same group as XBCP) | arXiv:2604.17632 | Apr 2026 | CSR-L / CS-MTEB; code-switched queries degrade strong multilingual retrievers up to 27% | Hindi not among the 9 languages |
| Indi-RomCoM (Das et al.) | arXiv:2606.30790 | Jun 2026 | romanised Indic-English instructions, 4 Indian langs; monotone degradation with mixing density | not search |
| VoiceAgentBench (Jain et al.; Krutrim) | arXiv:2510.07978 | Oct 2025 | 6k spoken agentic queries in en + hi, bn, ml, mr, ta, te; tool-selection / parameter-filling accuracy | not web search |
| MASSIVE-Agents (Kulkarni et al.; Amazon) | EMNLP 2025 Findings (2025.findings-emnlp.1099); arXiv ID not confirmed | 2025 | function calling in 52 langs; AST accuracy 57.4% en vs 6.8% am | Indic per-language not in abstract |
| **Lost in Execution: Multilingual Robustness of Tool Calling** (Luo, Kutralingam, Okoani, Xu, Wei, Hu) | arXiv:2603.05515 | Jan 2026 (v2 Jun 2026) | MLCL benchmark over **Chinese, Hindi, Igbo**; dominant failure = **parameter-value language mismatch** (model writes tool arguments in the user's language); inference-time fixes never recover English-level performance | generic tools, not search; the closest documented analogue of "agent searches in the wrong language" |
| ITC (Zhang, Zhu) | arXiv:2601.05366 | Jan 2026 | 3,571 real APIs, 17,540 tool tasks, 40 countries | languages not listed |
| TUCAN (Emanuilov) | arXiv:2506.23394 | Jun 2025 | Bulgarian tool-use; "language confusion when prompted in lower-resource languages" | not search |
| MMInA (Tian et al.) arXiv:2404.09992; MMSearch (Jiang et al.) arXiv:2409.12959; MMSearch-R1 arXiv:2506.20670; Mind2Web; GAIA (original) | | | all English-only in abstract; no multilingual Mind2Web or FRAMES found | |

Not found despite targeted searches: any Hindi/Tamil/Bengali BrowseComp; Search-R1 / ReSearch / R1-Searcher evaluated on Indic languages; multilingual FRAMES or Mind2Web; "SealQA" / "BrowseComp-VL" multilingual content.

---

## 4. Language of query formulation by LLM agents

| Paper | ID / venue | Date | Finding relevant to "does the agent search in English for an Indic question?" |
|---|---|---|---|
| **XRAG** (Liu et al.; Amazon) | arXiv:2505.10089; EMNLP 2025 Findings | May 2025 | The only published controlled query-language ablation on a real search engine: real non-English user queries (DE, ES, JP) sent to Google in native form vs English-translated form; native-only satisfied 59.8 / 61.1 / 57.9% vs English-only 56.3 / 44.3 / 48.4%; **union 71.5 / 68.3 / 68.9%**. English-only search loses the most for the script-distant language (Japanese, -16.8); the two query languages are complementary (+~10 pts). Not an agent's own choice; no Indic. |
| DELTA / DeLP (Park et al.) | arXiv:2601.02956; ACL 2026 Findings | Jan 2026 | English pivoting (translate query to English) is a strong heuristic (58.8%) but its gains are "primarily driven by retrieval-side structural biases" (exposure + gold-availability priors); a fused English + local query wins (62.9%). MKQA, no Indic. |
| Ranaldi, Haddow, Birch (tRAG/MultiRAG/CrossRAG) | arXiv:2504.03616; EACL 2026 Findings | Apr 2025 | query translation to English "suffers from limited coverage"; direct multilingual retrieval has inconsistency; translating retrieved docs wins. |
| Amiraz et al., Cross-Lingual Cost | arXiv:2507.07543 | Jul 2025 | the opposite sign: on ar/en enterprise corpora, translating the query is a *fix*; i.e., the sign depends on where the evidence lives -- which is exactly what an evidence-pool manipulation resolves. |
| Gupta et al., How and Where to Translate? | arXiv:2507.22923 | Jul 2025 | pre-translation vs cross-lingual prompting when the KB is English; cross-lingual prompting helps low-resource langs most. |
| Liu et al., Is Translation All You Need? | arXiv:2403.10258; NAACL 2025 | Mar 2024 | translate-to-English helps English-centric LLMs on standard tasks but not for culture-sensitive tasks or non-English-centric LLMs. |
| Etxaniz et al., self-translate | arXiv:2308.01223; NAACL 2024 | Aug 2023 | self-translation to English beats direct inference on 5 tasks. |
| Wendler et al., Do Llamas Work in English? | arXiv:2402.10588; ACL 2024 | Feb 2024 | middle layers decode the English token before the input-language token: the mechanistic prior for spontaneous English search strings. |
| Schut, Gal, Farquhar, Do Multilingual LLMs Think in English? | arXiv:2502.15603; ICLR 2025 | Feb 2025 | semantically loaded decisions made in English-like representations. |
| Marchisio et al., Language Confusion | arXiv:2406.20052; EMNLP 2024 | Jun 2024 | Language Confusion Benchmark, 15 languages; wrong-language outputs, worse for English-centric models and complex prompts; adaptable to tool arguments. |
| Li, Xu, Xie, Language Drift in mRAG | arXiv:2511.09984; AAAI 2026 | Nov 2025 | English is "both the strongest interference source and the most frequent fallback". |
| Lost in Execution / MLCL (Luo et al.) | arXiv:2603.05515 | Jan 2026 | parameter-value language mismatch in tool calls for Chinese, **Hindi**, Igbo -- the documented mechanism by which a search query would come out in the "wrong" language. |
| MAPS (Hofman et al.) | arXiv:2505.15935 | May 2025 | OpenDeepResearch plans align with English instructions in 85% of cases -- plan-level English bias incl. Hindi. |
| Pahuja et al., TART | arXiv:2608.03735 | Aug 2026 | information lost at plan -> tool-argument interface. |
| Chirkova et al. | arXiv:2407.01463 | Jul 2024 | entity spelling across scripts breaks matching; code-switching in non-Latin scripts. |
| Code-Switching IR (Zeng, Lu et al.) | arXiv:2604.17632 | Apr 2026 | half-translated (code-switched) queries hurt retrieval up to 27%. |
| M-Thinker (Zhang et al.) arXiv:2510.07300; Cross-lingual self-consistency (Elhady, Agirre, Artetxe) arXiv:2606.01464; Agarwal et al. enterprise consistency arXiv:2509.23659 (EMNLP 2025) | | 2025-26 | RL / alignment recipes that constrain reasoning language; could constrain query language. |
| Characterizing Web Search by Conversational LLM Agents (Amani et al.) | arXiv:2609.19244 | Sep 2026 | logs issued queries vs prompts for 4 chatbots; English only by its own limitations. |

**Bottom line for sec. 4:** as of 2026-10-10 no paper reports the statistic "fraction of search calls issued in English for Hindi/Indic user questions" for any LLM search agent, and no paper forces/ablates the agent's query language on a corpus whose evidence language is itself controlled. The closest are XRAG's Google experiment (fixed engine, 3 European/East-Asian languages), DELTA's English-pivot baseline (single-shot, MKQA), MLCL's parameter-language-mismatch finding (generic tools, Hindi included), and MAST-Indic (forthcoming shared-task notes).

---

## 5. Evidence / knowledge availability gaps

### 5a. Wikipedia article counts (MediaWiki siteinfo API, 2026-10-10; cross-checked with meta List_of_Wikipedias)

| Wikipedia | Articles | Active users (30d) | en / lang |
|---|---:|---:|---:|
| English | 7,250,566 | 271,802 | 1x |
| Urdu* | 705,006 | 396 | 10x |
| Bengali | 191,981 | 1,724 | 38x |
| Tamil | 191,118 | 505 | 38x |
| Hindi | 171,975 | 1,061 | 42x |
| Telugu | 129,609 | 396 | 56x |
| Marathi | 103,343 | 285 | 70x |
| Malayalam | 89,127 | 447 | 81x |
| Punjabi | 59,741 | 132 | 121x |
| Kannada | 34,687 | 247 | 209x |
| Gujarati | 30,934 | 90 | 234x |
| Odia | 21,129 | 63 | 343x |

*Urdu inflated by bot stubs (396 active users). Hindi has ~2.4% of English's article count; for most entities a Hindi article is absent or a stub, so **fact-level** (not article-level) coverage is the binding constraint when building an aligned pool.

### 5b. Web text (Common Crawl CC-MAIN-2026-39, % of pages, CLD2): en 41.86%; hi 0.215%; bn 0.110%; ta 0.045%; ur 0.031%; mr 0.026%; ml 0.022%; te 0.019%; kn 0.015%; gu 0.012%; pa 0.009%; or 0.007%. All 11 Indic ~0.51%; English ~195x Hindi, ~6,300x Odia. FineWeb-2 (arXiv:2506.20920) words: hi 11.2B, bn 6.2B, ur 2.7B, ta 1.9B, mr 1.5B, ml 1.05B, gu 0.93B, te 0.89B, kn 0.75B, pa 0.52B, or 0.33B (English FineWeb ~15T tokens, ~1,300x Hindi). Sangraha (arXiv:2403.06350) total 251B tokens over 22 langs of which **163B are synthetic (translated English)**, 64B verified native, 24B unverified; e.g. hi 34.5B total (12.6B verified), ta 17.4B (4.0B verified), te 16.3B (3.7B verified). IndicCorp v2 (arXiv:2212.05409): 20.9B tokens / 24 langs. Implication: "Indic knowledge" in Indic-LLM pretraining is largely translated English knowledge.

### 5c. Language-dependent factual recall (verified)

| Paper | ID / venue | Date | Finding |
|---|---|---|---|
| X-FACTR (Jiang, Anastasopoulos, Araki, Ding, Neubig) | arXiv:2010.06189; EMNLP 2020 | 2020 | cloze recall in 23 langs drops sharply for low-resource; code-switching partially recovers |
| mLAMA (Kassner, Dufter, Schütze) | arXiv:2102.00894; EACL 2021 | 2021 | 53-language LAMA; strong language bias |
| mParaRel (Fierro & Søgaard) | arXiv:2203.11552; ACL 2022 Findings | 2022 | consistency far lower outside English |
| Cross-Lingual Consistency of Factual Knowledge / RankC, BMLAMA (Qi, Fernández, Bisazza) | arXiv:2310.10378; EMNLP 2023 | 2023 | scale raises accuracy, not consistency; edits transfer only to languages with high RankC to English |
| Polyglot or Not? (Schott, Furman, Bhat) | arXiv:2305.13675; EMNLP 2023 | 2023 | 303k facts, 20 langs; non-English recall much lower |
| Crosslingual Capabilities and Knowledge Barriers (Chua et al.; Google/Princeton) | arXiv:2406.16135; NeurIPS-W 2024 | Jun 2024 | 15 models, 16 langs: QA in a language other than the one the knowledge was learned in shows a large gap; mixed-language training reduces it |
| Language Ranker (Li et al.) | arXiv:2404.11553; AAAI 2025 | 2024 | representation similarity to English tracks pretraining share |
| MLaKE (Wei et al.) | arXiv:2404.04990; COLING 2025 | 2024 | knowledge edits are language-local |
| How Do Multilingual LMs Remember Facts? (Fierro, Foroutan, Elliott, Søgaard) | arXiv:2410.14387 | Oct 2024 | subject enrichment language-independent; object extraction language-dependent |
| Global-MMLU (Singh et al.) | arXiv:2412.03304 | Dec 2024 | 28% of MMLU needs culture-specific knowledge; 84.9% of geographic items are NA/Europe |
| **ECLeKTic** (Goldman, Shaham, Malkin et al.; Google) | arXiv:2502.21228 | Feb 2025 | closed-book QA from Wikipedia articles existing in **only one** of 12 languages (Hindi incl.); LLMs fail to transfer; **the most direct template for an evidence-exists-only-in-language-X pool** |
| Do Multilingual LLMs Think in English? (Schut, Gal, Farquhar) | arXiv:2502.15603; ICLR 2025 | 2025 | English-like latent decisions |
| Lost in Multilinguality / KLAR (Wang et al.) | arXiv:2504.04264; ACL 2025 | Apr 2025 | parallel-fact set, 17 langs; failure at final-layer language transition |
| **MultiLoKo** (Hupkes & Bogoychev) | arXiv:2504.10356 | Apr 2025 | 31 langs incl. hi, bn, ta, te, mr, ur; locally-sourced vs translated partitions; language difficulty ranking changes (rank corr. 0.78); "mother tongue effect": models answer local questions better in the local language than in English translation |
| **Better To Ask in English?** (Rohera, Ginimav, Sawant, Joshi) | arXiv:2504.20022 | Apr 2025 | IndicQuest: same questions in en + 19 Indic; GPT-4o, Gemma-2, Llama-3.1 better in English even for India-rooted questions; more hallucination in Indic; **no retrieval** |
| Tracing Multilingual Factual Knowledge Acquisition (Liu et al.) | arXiv:2505.14824; EMNLP 2025 Findings | May 2025 | recall is frequency-driven and language-agnostic; cross-lingual transfer small |
| Paths Not Taken (Lu, Zhang, Eickhoff, Pavlick) | arXiv:2505.20546 | May 2025 | English-centric recall pathway then translate-back; failures at translate-back |
| Entity-Level Alignment in Crosslingual Consistency (Liu, Wang, Yvon, Schütze) | arXiv:2510.10280 | Oct 2025 | adding English entity names to prompts raises accuracy/consistency -- a cheap control for entity-recognition vs knowledge absence |
| Rethinking Cross-lingual Gaps from a Statistical Viewpoint (Piratla, Jain, Singh, Cohn, Jyothi, Talukdar) | arXiv:2510.15551 | Oct 2025 | the gap is mostly target-language *variance*; single-sample comparisons overstate it; sample multiple generations |
| **Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts** (Bandarkar, Ansell, Cohn) | arXiv:2603.17070; EMNLP 2026 Findings | Mar 2026 | on ECLeKTic + MultiLoKo, **script mismatch** predicts transfer failure better than language family; supplying source-language entity names helps cross-script questions disproportionately |
| **IndicKLAR** (Mazumder, Pathak, Kodali, Joshi, Agarwal, Patro) | arXiv:2605.29637; EMNLP 2026 Findings | May 2026 | KLAR extended to 18 Indian langs + 11 code-mixed pairs; native-script vs English gap up to ~0.50 across 9 open models; code-mixing shrinks it to ~0.05 |
| PolyFact (von Rad et al.) | arXiv:2606.06586 | Jun 2026 | 60k parallel Wikidata facts, 12 langs; consistency-reward GRPO |
| Cross-Lingual Exploration for Parametric Knowledge (Diskind, Trainin, Shaham, Choshen, Szpektor, Abend) | arXiv:2606.24579 | Jun 2026 | language-specific knowledge pockets; multi-language prompting recovers more facts |
| L3Cube-IndicQuest v2 (Jain, Mahajan, Joshi, Joshi) | arXiv:2608.15535 | Aug 2026 | 3,471 India-centric QA x 20 langs; hi/mr "moderate", or/ur "extremely low" |
| SWORD (Park, Kang, Kwak, Yun) | arXiv:2609.09349 | Sep 2026 | cross-lingual false-fact rejection via Wikidata distortions |
| Muller et al., Attribution for Cross-Lingual QA | arXiv:2305.14332; EMNLP 2023 | 2023 | XOR-TyDi (bn, te, fi, ja, ru): up to ~50% of exact-match answers not attributable to any retrieved passage -> parametric memory confounds "retrieval success"; **mandatory control** |

### 5d. Wikipedia/Wikidata coverage and local-vs-global knowledge

Hecht & Gergle, *Tower of Babel Meets Web 2.0* (CHI 2010; self-focus bias of each edition); Kaffee et al., *A Glimpse into Babel* (OpenSym 2017; Wikidata label coverage maldistributed; Hindi 18.2% figure **UNVERIFIED**); Roy, Bhatia, Jain, *Topic-Aligned Multilingual Corpus of Wikipedia Articles for Studying Information Asymmetry in Low Resource Languages* (LREC 2020, incl. Hindi; closest precedent for en/hi aligned article pairs); WikiGap (Wang et al.; arXiv:2505.24195; May 2025; non-English editions contain facts English lacks -> the gap runs both ways); Kronk, *Bias in Coverage of Humans in Wikidata* (arXiv:2609.22375; Sep 2026); BLEnD (Myung et al.; arXiv:2406.09948; NeurIPS 2024 D&B; performance tracks online representation of a culture); XLQA (Roh, Ju, Lee; arXiv:2508.16139; EMNLP 2025; locale-dependent answers -> exclude such items); **WILA-PopQA** (Iferroudjene et al.; aclanthology 2026.kallm-1.19, KG-LLM @ LREC 2026; Wikidata biographical QA in 9 langs incl. **Hindi**, popularity-controlled, explicit **language-of-entity x language-of-question** factorial over 12 open models; question language dominates, matching entity language does not reliably help; **closed-book, no retrieval**); RiDiC (Braslavski et al.; arXiv:2604.00019; LREC 2026; popularity-controlled entity sampling pipeline). "KnowLang" did not resolve to any paper (UNVERIFIED; likely MultiLoKo was meant).

---

## 6. Critical pre-emption check: does anyone already separate a "query gap" from an "evidence gap"?

Phrasings searched (standard + extended): "query gap evidence gap multilingual"; "retrieval failure attribution multilingual RAG"; "error decomposition multilingual QA retrieval vs knowledge"; "oracle retrieval multilingual RAG gap"; "corpus coverage vs retriever multilingual"; "search agent failure taxonomy query formulation evidence corpus coverage"; "agentic RAG multilingual query language ablation English queries"; "Indian languages / Indic search agent deep research benchmark 2026"; "same questions multiple languages web search agent accuracy"; "LLM agents search in English for non-English users"; "answerable only English evidence low-resource upper bound"; "multilingual QA oracle passage retrieval error vs knowledge Hindi Bengali Telugu"; plus Semantic Scholar queries (rate-limited after one return).

**Result: no paper crosses (question language) x (agent query language, observed then forced) x (evidence-pool language) for an LLM search agent, in any language; and no agentic paper does any two of these three for an Indic language.** The nearest five and exactly what each does not do:

| # | Nearest paper | What it does | What it does NOT do |
|---|---|---|---|
| 1 | **XBCP** (Lu et al., arXiv:2606.15345, Jun 2026) | Agentic deep research on a fixed corpus whose evidence language is varied (12 langs); oracle-retrieval decomposition into retrieval/search bottleneck vs evidence-integration bottleneck; search-call counts; reasoning-trace query expansion | Question language never varies (always English); never measures or forces the agent's query language; no Indic language (4 African low-resource); evidence is machine-translated, not native; the decomposition is retrieval-vs-integration, not query-side-vs-corpus-side; fixed corpus only |
| 2 | **MarathiWeb** (Kale, SIGIR 2026, DOI 10.1145/3805712.3808534) | Native Marathi local vs translated global queries; two web-search LLMs vs Google baseline; attributes failures to "evidence integration rather than missing sources"; finds one-call retrieval beats multi-step | One language; two models; live web only, so evidence availability is observed not manipulated; no query-language logging or forcing reported; no parallel English arm in abstract; attribution is by inspection, not by factorial design |
| 3 | **MAST @ FIRE 2026, Indic track** (Thakur, Zhang, Sharifymoghaddam, Ma, Chen, Lin) | 9 Indic query languages, English BrowseComp-Plus corpus, iterative agents, Recall + EM; explicitly discourages query translation as the only strategy | English-only corpus, so the evidence gap is zero by construction and cannot be measured; a systems shared task, not an attribution study; overview not yet published (working notes due 2026-10-15, so participant notes on query-translation strategies will exist within weeks) |
| 4 | **DeLP / DELTA** (Park, Kim, Hwang, Lee, arXiv:2601.02956, ACL 2026 Findings) | Names the confound (gold-availability prior + exposure prior vs genuine model preference); regression-based debiasing; English-pivot vs fused query comparison | Single-shot retriever, no agent, no iterative search; no experimental manipulation of the evidence pool (statistical correction instead); MKQA, so no Indic language; does not log what language a model would *choose* to query in |
| 5 | **Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents** (Liu, Mao, Zhu, Chua, arXiv:2608.01913, Aug 2026) | Every agent failure labelled retrieval gap (never found; oracle evidence) vs utilization gap (found, misused); 6 agents, BrowseComp(-Plus) | English only; "retrieval gap" is not split into query-formulation vs corpus-coverage; no language variable at all. Terminology overlap: avoid calling ours a "retrieval gap" |

Also adjacent (each missing two of the three factors): Amiraz et al. (arXiv:2507.07543; true query-language x document-language 2x2 for ar/en, single-shot, evidence present in both languages by construction); XRAG (arXiv:2505.10089; native vs English Google queries, fixed engine, de/es/ja); Ranaldi et al. (arXiv:2504.03616; tRAG vs MultiRAG vs CrossRAG, single-shot; attributes tRAG's weakness to "limited coverage" without measuring it); CORAL (arXiv:2604.25676; agent chooses corpus language, reports only end accuracy); HyperBrowseComp (arXiv:2610.03574; native non-English browsing questions, no Indic, no parallel versions, no decomposition); MLCL / Lost in Execution (arXiv:2603.05515; tool-argument language mismatch incl. Hindi, not search); WILA-PopQA (KG-LLM 2026; language-of-entity x language-of-question incl. Hindi, closed-book); Better To Ask in English? (arXiv:2504.20022; parallel en/Indic parametric accuracy, no retrieval); Health-Pariksha (arXiv:2410.13671; Indic RAG with real queries, fixed pipeline); Muller et al. (arXiv:2305.14332; non-attributable answers in XOR-TyDi bn/te -- parametric leakage control).

---

## 7. Practical tooling (checked 2026-10-10; details and sources in the tooling sub-report)

### 7a. Web-search APIs: price, free tier, language/country targeting

| API | Free tier | Paid / 1k queries | Language param | Country param | Content | 10k searches cost | Fits $30? |
|---|---|---|---|---|---|---|---|
| Perplexity Search API (standalone) | none found | **$1 (fast)** / $5 (standard) | `search_language_filter` (ISO 639-1, up to 20) | `country`, `user_location` | snippets + dates | **$10** | Yes |
| Parallel.ai Search | up to $80 signup + $5/mo | **$1 (turbo/fast)** / $5 (basic/adv.) | none | `location` (ISO country) | LLM-optimised excerpts | $10 (or $0 on credit) | Yes (no language targeting) |
| You.com | $100 signup credit (blog, 2026-03); MCP 100/day | $5 | `language` (BCP-47) | `country` (incl. IN) | snippets; `extraction: full_page` | $50 list / $0 on credit | Yes via credit |
| Exa | $10 credits/month | $4 instant; $7 auto; $12 deep | **none** | `userLocation` | text/highlights via contents ($1/1k pages) | $30 | Exactly (no language) |
| Valyu | ~$10-20 signup (UNVERIFIED) | $1.50 web | none | `country_code` | full markdown | $15 | Yes (no language) |
| Linkup | 4,000 free | $5-6 | none | none | content snippets | $30 | Exactly |
| Brave Search API | $5 credit/month (~1k) | $5 | `search_lang` (filters by content language), `ui_lang` | `country` | snippets + `extra_snippets` | $45 | No |
| Tavily | 1,000 credits/month | $8 basic / $16 advanced | `language` (+`filter_by_language: true`) | `country` (incl. india) | `content`, `raw_content` | $72 | No |
| Serper.dev | 2,500 free | $1 but **$50 minimum pack** | Google `hl` (param names from wrappers) | `gl`, `location` | Google snippets | $50 min | No (pilot only) |
| Jina s.jina.ai | ~1,000 free (10k tokens/search) | ~$0.50 (UNVERIFIED), **$50 minimum** | `hl`/`gl`/`X-Locale` listed | `gl`, `location` | **top-5 full-page markdown** | $50 min | No |
| SerpAPI | 250/month | $25 -> $10 | `hl`, `lr` (lang_hi, lang_bn) | `gl`, `location`, `uule` | Google snippets | $150+ | No |
| Firecrawl /search | 1,000 credits/mo (~500 searches) | ~$10 | no `lang` in current API ref (UNVERIFIED) | `country`, `location` | + scrape markdown | ~$80 | No |
| Google Custom Search JSON | 100/day but **closed to new customers**; sunset 2027-01-01 | $5 | `lr` list has no Indic codes | `gl`, `cr` | snippets | n/a | No |
| Bing Web Search API | **retired 2025-08-11** | - | - | - | - | - | - |
| DuckDuckGo (`ddgs`, unofficial) | free | $0 | `region` (e.g. in-en) | same | snippets | $0 | Yes, not reproducible |
| SearXNG self-hosted | free; ~$5 VPS | $0 | `language` locale (hi, bn, ...) | via locale | JSON (enable `formats`) | ~$5 | Yes; upstream CAPTCHA risk |
| OpenRouter `:online` / web plugin | - | $7 (Exa-backed, $0.007/req) + LLM tokens | none | none | injected into prompt | $70 | No |

Only Perplexity Search (fast), You.com (on credit), Brave, and Tavily combine an explicit **language** parameter with a price that is anywhere near $30 for 10k queries; Exa/Parallel/Valyu/Linkup/OpenRouter cannot target language, which confounds the query-language factor in a live-web arm. Search engines also return different result sets day to day, so a live-web arm cannot be the primary instrument for a factorial design.

### 7b. Offline evidence corpora

| Resource | Snapshot | Indic sizes | Notes |
|---|---|---|---|
| HF `wikimedia/wikipedia` | **20231101 only** (no newer configs) | articles: hi 163,093 (238 MB parquet); bn 143,069 (344); ta 160,651 (266); te 87,854 (215); mr 94,133 (82); kn 31,437 (147); ml 85,791 (183); gu 30,445 (40); pa 51,423 (81); or 17,375 (27); ur 200,154 (168); en 6,407,814 (11.6 GB) | cc-by-sa-3.0 |
| HF `omarkamali/wikipedia-monthly` | **20261001** (348 langs, updated 2026-10-09) | hi 185,949 rows / 312 MB; bn 208,062 / 622 MB; ta 208,298 / 364 MB; te 145,514 / 428 MB; en 7,265,754 / 15.5 GB | CC-BY-SA-4.0; best current snapshot |
| HF `wikimedia/structured-wikipedia` | 2026-05 | **en + fr only** | has Wikidata IDs, infoboxes; no Indic |
| MIRACL corpus (`miracl/miracl-corpus`) | hi Mar-2022; bn, te Feb-2019 | hi 506k passages / 148k articles; bn 297k / 64k; te 518k / 66k; en 32.9M / 5.76M | prebuilt Pyserini BM25 indexes `miracl-v1.0-{hi,bn,te}` |
| IndicCorp v2 (`ai4bharat/IndicCorpV2`) | 2022-23 | 20.9B tokens / 24 langs; hi ~152M sentences, bn ~29.6M, ta ~20.8M, te ~31M, mr ~27.8M, kn ~48.7M, ml ~48.1M | CC-0 |
| Sangraha (`ai4bharat/sangraha`) | 2024 | 251B tokens total (64B verified native, 163B synthetic/translated); hi 34.5B, bn 30.0B, ta 17.4B, gu 17.2B, ml 16.4B, te 16.3B, ur 14.4B, mr 14.3B, kn 14.3B, or 12.5B, pa 11.2B | CC-BY-4.0 |
| mMARCO (`unicamp-dl/mmarco`) | 2021 | Hindi only among Indic; 8.84M passages | Apache-2.0 |
| IndicMSMarco (`ai4bharat/IndicMSMarco`) | 2025 | 13 Indic langs, 1,000 human-post-edited parallel queries each | see sec. 1 |
| Wikidata sitelinks | weekly JSON dump (~130 GiB gz) or SPARQL (60 s/query, 5 parallel/IP) | `schema:about` / `schema:isPartOf <https://hi.wikipedia.org/>` | the join key for "same entity, en vs hi article" |

Retrievers: BM25 via Pyserini/Anserini `--language hi|bn|te` (Lucene analyzers; **no Tamil analyzer** -- use bm25s with a custom tokenizer or ICU); dense via bge-m3 (MIT), multilingual-e5-large/small (MIT), Qwen3-Embedding-0.6B (Apache-2.0); jina-embeddings-v3 is CC-BY-NC. Modal Starter gives **$30/month free credit** (A10 $0.000306/s), enough to embed ~1M passages at zero budget cost; API embedders for 1M passages: OpenAI text-embedding-3-small ~$6, Voyage 3.5-lite ~$2-6 (first 200M tokens free), Cohere embed-v4 ~$30-36 (UNVERIFIED per-token price).

**Cheapest reproducible setup:** build en + Indic Wikipedia pools from `omarkamali/wikipedia-monthly` 20261001, align entities with Wikidata sitelinks, index with BM25 (Pyserini) and bge-m3 on Modal's free credit, expose the index to the agent as a single `search(query, lang)` tool. Spend the $30 on LLM tokens through OpenRouter. If a small live-web validation arm is wanted, Perplexity Search `fast` ($1/1k with `search_language_filter` + `country`) is the only option that is both cheap and language-targetable.

---

## 8. Pre-emption verdict: **ALIVE-BUT-CROWDED**

Reasoning. The core factorial (parallel questions; question language x agent query language x evidence-pool language; agent's query language logged, then forced) has not been run for any language, and not for Indic languages in any partial form. But in the last five months the field has converged on the components: XBCP supplies the fixed-corpus, language-varied, oracle-decomposed *agentic* paradigm (English questions, no Indic); MarathiWeb supplies a native Indic web-search-LLM evaluation with an informal missing-sources-vs-integration attribution; MAST-Indic will shortly produce nine-language Indic agentic-search results with query-translation strategies described by participants; DELTA supplies the vocabulary ("gold-availability prior" vs model preference); and Liu et al. / SearchAuditor / CIVI supply retrieval-gap-vs-utilization-gap taxonomies for English agents. A reviewer will see the proposed paper as "XBCP with the question language flipped, on Indic languages" unless the contribution is pinned to the two things none of them has: (i) the agent's **query-language choice as a measured mediator and then as a manipulated factor**, and (ii) a **coverage x conditional-accuracy decomposition** that puts a number on how much of the Indic accuracy drop is corpus coverage versus agent behaviour. Timing matters: MAST working notes are due 2026-10-15 and the FIRE overview will follow; a workshop submission should be out before participants publish query-language analyses as side results.

What makes it DEAD: if the paper's claim is only "search agents do worse on Hindi questions and oracle evidence closes most of the gap" -- XBCP (for 12 non-Indic languages) and MarathiWeb (for Marathi) already say that. What keeps it ALIVE: the decomposition and the mediator, on native Indic evidence, with parallel questions.

---

## 9. Recommended sharpening

### 9a. Problem statement (sharpened)

"When a user asks an LLM search agent a question in an Indic language, how much of the accuracy loss relative to the same question in English is due to (a) the agent's query behaviour -- it formulates worse queries or searches in a language where the evidence is not -- versus (b) the evidence simply not existing in that language? We hold question content fixed with parallel questions, hold the evidence pool fixed with aligned English/Indic Wikipedia corpora in which we control which language(s) the gold evidence exists in, log the language of every search call the agent issues, and then force the query language. This yields a two-term decomposition of the real-world gap: Acc_L = Cov_L * Acc(L | evidence present in L) + (1 - Cov_L) * Acc(L | evidence only in English), where Cov_L is measured on the live Indic Wikipedia and the conditional accuracies come from the controlled experiment."

Distinct from XBCP because the user question (not the corpus) is what varies and the agent's own language choice is the object of study; distinct from MAST because the evidence pool language is manipulated; distinct from DELTA/Amiraz because the system is an iterative agent and the manipulation is experimental, not statistical; distinct from MarathiWeb because attribution is by design, across 2-3 languages, with parallel English arms. Naming: do not reuse "retrieval gap" (Liu et al. 2026). Suggested terms: **query-side gap** (QG) and **evidence-side gap** (EG), with the XBCP-style **integration gap** (IG) as the residual under oracle evidence.

### 9b. Cleanest factorial design (workshop scale, $30)

Languages: Hindi (largest Indic Wikipedia, Devanagari) + one Dravidian language with a MIRACL corpus and XOR-TyDi lineage (Telugu) or the largest Dravidian Wikipedia (Tamil). Two languages are enough for a workshop paper; a third (Bengali) if budget allows.

Questions: 150-200 per language, parallel in English and L. Three sources, each with known gold evidence location:
- MLQA-hi items (gold paragraph is genuinely parallel in en and hi Wikipedia) -- the cleanest "evidence in both" cell;
- IndicGenBench XorQA-In / XOR-TyDi te/bn items (gold is an English Wikipedia passage; Indic counterpart located via Wikidata sitelink, present or absent) -- natural "evidence only in English" cell;
- MultiLoKo local-partition hi/te/ta items or IndicQuest v2 India-centric items with a verified Indic-Wikipedia gold passage -- the "local knowledge, evidence naturally in L" cell. Exclude locale-dependent-answer items (XLQA warning). Verify no parametric leakage with a closed-book run; report attribution rate (Muller et al.).

Evidence pool E (fixed, offline, one `search(query, lang)` tool over Wikipedia-monthly 20261001 chunks, BM25 + bge-m3 hybrid): **EN-only** (gold present only in English pool; Indic pool present but gold article removed), **L-only** (gold present only in Indic pool), **BOTH**, plus **NONE** as a parametric baseline on a 50-item subset.

Question language Q: **en** vs **L** (parallel).

Query policy P: **free** (agent chooses; log language of every query via script detection), **match** (system prompt forces queries in the question language), **english** (forces English queries), **dual** (forces each search to be issued in both languages). Policies are prompt-level, which is realistic for API models; verify compliance from logs.

Core cells: Q(2) x E(3) x P(free, english, match) = 18 cells x 150 items x 2 languages = 5,400 episodes per model; with a cheap model at ~8k tokens/episode (5 searches, 5 reads) that is ~43M tokens. On OpenRouter a budget open-weight or flash-tier model at roughly $0.2-0.6 per M tokens gives ~$10-25 per model (check live prices at run time); use a fractional design (drop P=match for Q=en, and run P=dual only on E=BOTH) to fit two models. Judge with alias-aware exact match (free), LLM-judge only on disagreements.

Estimands:
- **Query-side gap**: Acc(Q=en, E=BOTH, free) - Acc(Q=L, E=BOTH, free). Same evidence, same content; only the question language (and so the agent's behaviour) differs. Mediator: fraction of search calls in English, retrieval hit rate of gold passage per call. **Recoverable QG** = gain from P=english (or P=dual) at E=BOTH. Residual under oracle evidence = integration gap.
- **Evidence-side gap (controlled)**: Acc(Q=L, E=BOTH) - Acc(Q=L, E=L-only) [cost of having no English evidence to cross to] and Acc(Q=L, E=BOTH) - Acc(Q=L, E=EN-only) [cost of having no in-language evidence]; the P x E interaction tells whether forcing English queries helps (E=EN-only) or hurts (E=L-only).
- **Evidence-side gap (in the wild)**: Cov_L = fraction of gold facts in the question set whose supporting sentence exists in live L-Wikipedia (sitelink + answer-string check, manual spot-check of 50); combine with the conditional accuracies above to report what share of the real gap is coverage.
- **Symmetric monolingual check**: Acc(Q=en, E=EN-only, match) vs Acc(Q=L, E=L-only, match) with gold present in both -- isolates Indic-script retrieval + passage-reading cost from any cross-lingual issue; run with BM25 vs bge-m3 to see how much is the retriever.

### 9c. Pre-registrable directional hypotheses

- **H1 (query language drift).** Under P=free with Q=L, API agents issue English search queries for a majority of search calls (>50%) and the English fraction is higher for the lower-resource language (te/ta) than for Hindi. Mechanistic priors: Wendler et al. 2024; MLCL parameter-language mismatch (Hindi); MAPS plan-level English bias.
- **H2 (query-side gap exists and is partly recoverable).** Acc(Q=en, E=BOTH) - Acc(Q=L, E=BOTH) > 0, and P=dual recovers at least half of it; P=english recovers less than P=dual (XRAG union effect: +~10 pts over either single language).
- **H3 (policy x evidence interaction).** Forcing English queries improves accuracy when E=EN-only and *reduces* it when E=L-only, i.e. the sign of "should the agent translate the query" is determined by where the evidence lives (reconciles Amiraz et al. vs Ranaldi et al.).
- **H4 (coverage dominates in the wild for lower-resource languages).** Cov_L for India-centric questions is below 0.5 for te/ta and higher for hi, so the coverage term accounts for a larger share of the real-world gap than the query-side term for te/ta but not for hi.
- **H5 (retriever, not reader, carries the symmetric gap).** In the symmetric monolingual check, the hi/te deficit is larger under BM25 than under bge-m3, and shrinks further under oracle passages, i.e. most of it is script-level retrieval, not reading.
- **H6 (integration gap is small relative to query-side gap for frontier models).** Under oracle evidence, Q=L accuracy is within 5 points of Q=en (contrast with XBCP's finding that translated evidence still hurts: here the question, not the evidence, is non-English).

Falsification is cheap: H1 falsified if free-policy query language tracks question language; H3 falsified if P=english helps uniformly; H4 falsified if Cov_L > 0.7 for all three languages.

---

## 10. Candidate references (arXiv IDs verified unless marked)

Agentic search / deep research
1. Lu et al., Beyond Monolingual Deep Research: Cross-Lingual BrowseComp-Plus (XBCP). arXiv:2606.15345.
2. Chen, Ma, Zhuang et al., BrowseComp-Plus. arXiv:2508.06600.
3. Zhou et al., BrowseComp-ZH. arXiv:2504.19314.
4. Lee et al., K-BrowseComp. arXiv:2606.02404.
5. Aji et al., HyperBrowseComp. arXiv:2610.03574.
6. Wong et al., WideSearch. arXiv:2508.07999.
7. Wu et al., WebWalker / WebWalkerQA. arXiv:2501.07572.
8. Tongyi DeepResearch Team, Technical Report. arXiv:2510.24701.
9. Liu, Mao, Zhu, Chua, Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents. arXiv:2608.01913.
10. Liang et al., SearchAuditor. arXiv:2608.05212.
11. Liu, Zhong, Zhang, Li, CIVI. arXiv:2609.08094.
12. Amani et al., Characterizing Web Search by Conversational LLM Agents. arXiv:2609.19244.
13. Miroyan et al., Search Arena. arXiv:2506.05334.
14. Coelho et al., DeepResearchGym. arXiv:2505.19253.
15. Kale, Local Information Access in Marathi (MarathiWeb). SIGIR 2026, DOI 10.1145/3805712.3808534. **No arXiv; author from researchr only.**
16. Thakur, Zhang, Sharifymoghaddam, Ma, Chen, Lin, MAST @ FIRE 2026. mast-benchmark.github.io. **Shared task; no paper yet.**
17. Hofman et al., MAPS. arXiv:2505.15935.
18. Kim, Uhlig, Wuebker, GAIA-v2-LILT. arXiv:2604.24929.
19. Caciolai et al., OmnilingualGAIA2. arXiv:2608.08775.
20. Pahuja et al., Actionable Diagnosis of Multilingual Multi-Agent Planning Failures. arXiv:2608.03735.
21. Kuang et al., BabelArena. arXiv:2609.23490.
22. Luo et al., Lost in Execution (MLCL). arXiv:2603.05515.

Multilingual RAG / CLIR
23. Park & Lee, Investigating Language Preference of Multilingual RAG Systems. arXiv:2502.11175.
24. Park, Kim, Hwang, Lee, DeLP / DELTA. arXiv:2601.02956.
25. Wang et al., All Languages Matter (LAURA). arXiv:2604.20199.
26. Wu et al., Not All Languages are Equal (Futurepedia). arXiv:2410.21970.
27. Li et al., BordIRlines. arXiv:2410.01171.
28. Ranaldi, Haddow, Birch, Multilingual RAG for Knowledge-Intensive Task (tRAG/MultiRAG/CrossRAG). arXiv:2504.03616.
29. Qi, Fernández, Bisazza, Consistency of Multilingual Context Utilization in RAG. arXiv:2504.00597.
30. Liu et al., XRAG. arXiv:2505.10089.
31. Amiraz et al., The Cross-Lingual Cost. arXiv:2507.07543.
32. Moon, Kim, Verma, QTT-RAG. arXiv:2510.23070.
33. Li, Xu, Xie, Language Drift in Multilingual RAG. arXiv:2511.09984.
34. Lee, Song, Kang, CORAL. arXiv:2604.25676.
35. Ki et al., Linguistic Nepotism. arXiv:2509.13930.
36. Sharma, Murray, Xiao, Faux Polyglot. arXiv:2407.05502.
37. Chirkova et al., RAG in Multilingual Settings. arXiv:2407.01463.
38. Goworek, Macmillan-Scott, Özyiğit, Bridging Language Gaps (CLIR survey). arXiv:2510.00908; What Drives Cross-lingual Ranking? arXiv:2511.19324; Generative Query Expansion for CLIR arXiv:2511.19325.
39. Asenov et al., Retrieval or Representation? arXiv:2603.04238.
40. Jang et al., MLAIRE. arXiv:2605.07249.
41. Zeng, Lu et al., Code-Switching Information Retrieval. arXiv:2604.17632.
42. Qi et al., CroSearch-R1. arXiv:2604.25182; LcRL arXiv:2601.14896.
43. Muller et al., Evaluating and Modeling Attribution for Cross-Lingual QA. arXiv:2305.14332.
44. Wu, Ren, Verberne, Limits of Cross-lingual DPR for Low-Resource Languages. arXiv:2408.11942.

Query / reasoning language
45. Wendler et al., Do Llamas Work in English? arXiv:2402.10588.
46. Schut, Gal, Farquhar, Do Multilingual LLMs Think in English? arXiv:2502.15603.
47. Etxaniz et al., Do Multilingual LMs Think Better in English? arXiv:2308.01223.
48. Liu et al., Is Translation All You Need? arXiv:2403.10258.
49. Gupta et al., How and Where to Translate? arXiv:2507.22923.
50. Marchisio et al., Language Confusion. arXiv:2406.20052.

Benchmarks (Indic / multilingual QA & IR)
51. Zhang et al., MIRACL. arXiv:2210.09984.
52. Asai et al., XOR QA. arXiv:2010.11856.
53. Longpre, Lu, Daiber, MKQA. arXiv:2007.15207.
54. Lewis et al., MLQA. arXiv:1910.07475.
55. Artetxe, Ruder, Yogatama, XQuAD. arXiv:1910.11856.
56. Clark et al., TyDi QA. TACL 2020 (aclanthology 2020.tacl-1.30).
57. Doddapaneni et al., IndicXTREME / IndicQA / IndicCorp v2. arXiv:2212.05409.
58. Singh et al., IndicGenBench. arXiv:2404.16816.
59. Haq, Sharma, Bhattacharyya, IndicIRSuite. arXiv:2312.09508.
60. Prasanjith et al., IndicRAGSuite / IndicMSMarco. arXiv:2506.01615.
61. Thakur et al., MIRAGE-Bench. arXiv:2410.13716.
62. Bonifacio et al., mMARCO. arXiv:2108.13897.
63. Ruder et al., XTREME-UP. arXiv:2305.11938.
64. Bandarkar et al., Belebele. arXiv:2308.16884.
65. Verma et al., MILU. arXiv:2411.02538.
66. Watts et al., Pariksha. arXiv:2406.15053.
67. Gumma, Raghunath, Jain, Sitaram, Health-Pariksha. arXiv:2410.13671.
68. Hengle et al., MLNeedle. arXiv:2408.10151.
69. Kamath et al., ChatRAG-Hi. arXiv:2508.19831.
70. Reza, Maria, Nimi, AgriTrust-RAG. arXiv:2608.14886.

Knowledge / evidence gaps
71. Hupkes & Bogoychev, MultiLoKo. arXiv:2504.10356.
72. Goldman et al., ECLeKTic. arXiv:2502.21228.
73. Rohera et al., Better To Ask in English? (IndicQuest). arXiv:2504.20022; IndicQuest v2 arXiv:2608.15535.
74. Mazumder et al., IndicKLAR. arXiv:2605.29637.
75. Bandarkar, Ansell, Cohn, LRMs Struggle to Transfer Parametric Knowledge Across Scripts. arXiv:2603.17070.
76. Chua et al., Crosslingual Capabilities and Knowledge Barriers. arXiv:2406.16135.
77. Qi, Fernández, Bisazza, Cross-Lingual Consistency of Factual Knowledge (RankC). arXiv:2310.10378.
78. Jiang et al., X-FACTR. arXiv:2010.06189.
79. Kassner, Dufter, Schütze, mLAMA. arXiv:2102.00894.
80. Wang et al., Lost in Multilinguality (KLAR). arXiv:2504.04264.
81. Lu, Zhang, Eickhoff, Pavlick, Paths Not Taken. arXiv:2505.20546.
82. Liu, Wang, Yvon, Schütze, Entity-Level Alignment in Crosslingual Consistency. arXiv:2510.10280.
83. Piratla et al., Rethinking Cross-lingual Gaps from a Statistical Viewpoint. arXiv:2510.15551.
84. Singh et al., Global-MMLU. arXiv:2412.03304.
85. Myung et al., BLEnD. arXiv:2406.09948.
86. Roh, Ju, Lee, XLQA. arXiv:2508.16139.
87. Wang et al., WikiGap. arXiv:2505.24195.
88. Iferroudjene et al., WILA-PopQA. aclanthology 2026.kallm-1.19. **No arXiv found.**
89. Roy, Bhatia, Jain, Topic-Aligned Multilingual Wikipedia Corpus for Information Asymmetry. LREC 2020 (aclanthology 2020.lrec-1.289).
90. Hecht & Gergle, Tower of Babel Meets Web 2.0. CHI 2010. **No arXiv.**
91. Khan, Mehta et al., IndicLLMSuite / Sangraha. arXiv:2403.06350.
92. Penedo et al., FineWeb2. arXiv:2506.20920.

Unverified or non-arXiv items flagged above: xbench-DeepSearch (GitHub only); MASSIVE-Agents arXiv ID (ACL Anthology entry only); BharatBench (Krutrim tech report); Kaffee et al. Hindi-label 18.2% figure; MarathiWeb author list; "KnowLang" (no such paper found); M4-RAG and BabelArena Indic membership; HPLT/mC4 per-language Indic token counts; Serper/Jina parameter semantics and Jina/Valyu/Cohere prices.
