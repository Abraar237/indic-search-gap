# Reference verification (2026-10-10)

Every arXiv id in `references.bib` was fetched from the arXiv API by `lit_review/verify_refs.py` (title, authors, date recorded in `lit_review/lit_review.csv`, column `verified`). Two ids the seed sweep had swapped (2601.05366, 2603.05515) were corrected by hand against their abs pages. Non-arXiv entries (MarathiWeb DOI 10.1145/3805712.3808534, MAST shared-task site, TyDi QA TACL 2020, Hecht and Gergle CHI 2010, wikipedia-monthly dataset card, BM25 FnTIR 2009, Benjamini-Hochberg 1995) were checked against the publisher or project page.

Cited keys: 61; bib entries: 155; cited keys missing from the bib: ['a2610_00606']

| key | arXiv id | verified title |
|---|---|---|
| a1910_07475 | 1910.07475 | MLQA: Evaluating Cross-lingual Extractive Question Answering OK |
| a1910_11856 | 1910.11856 | On the Cross-lingual Transferability of Monolingual Representations OK |
| a2010_06189 | 2010.06189 | X-FACTR: Multilingual Factual Knowledge Retrieval from Pretrained Language Models OK |
| a2010_11856 | 2010.11856 | XOR QA: Cross-lingual Open-Retrieval Question Answering OK |
| a2102_00894 | 2102.00894 | Multilingual LAMA: Investigating Knowledge in Multilingual Pretrained Language Models OK |
| a2210_03629 | 2210.03629 | (manual entry)  |
| a2210_09984 | 2210.09984 | Making a MIRACL: Multilingual Information Retrieval Across a Continuum of Languages OK |
| a2305_14332 | 2305.14332 | Evaluating and Modeling Attribution for Cross-Lingual Question Answering OK |
| a2312_09508 | 2312.09508 | IndicIRSuite: Multilingual Dataset and Neural Information Models for Indian Languages OK |
| a2402_03216 | 2402.03216 | M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation OK |
| a2404_16816 | 2404.16816 | IndicGenBench: A Multilingual Benchmark to Evaluate Generation Capabilities of LLMs on Indic Languages OK |
| a2406_16135 | 2406.16135 | Crosslingual Capabilities and Knowledge Barriers in Multilingual Large Language Models OK |
| a2407_03618 | 2407.03618 | (manual entry)  |
| a2408_09437 | 2408.09437 | Hindi-BEIR : A Large Scale Retrieval Benchmark in Hindi OK |
| a2410_13671 | 2410.13671 | HEALTH-PARIKSHA: Assessing RAG Models for Health Chatbots in Real-World Multilingual Settings OK |
| a2411_02538 | 2411.02538 | MILU: A Multi-task Indic Language Understanding Benchmark OK |
| a2502_11175 | 2502.11175 | Investigating Language Preference of Multilingual RAG Systems OK |
| a2502_21228 | 2502.21228 | ECLeKTic: a Novel Challenge Set for Evaluation of Cross-Lingual Knowledge Transfer OK |
| a2504_03616 | 2504.03616 | Multilingual Retrieval-Augmented Generation for Knowledge-Intensive Task OK |
| a2504_10356 | 2504.10356 | MultiLoKo: a multilingual local knowledge benchmark for LLMs spanning 31 languages OK |
| a2504_19314 | 2504.19314 | BrowseComp-ZH: Benchmarking Web Browsing Ability of Large Language Models in Chinese OK |
| a2504_20022 | 2504.20022 | Better To Ask in English? Evaluating Factual Accuracy of Multilingual LLMs in English and Low-Resource Languages OK |
| a2505_10089 | 2505.10089 | XRAG: Cross-lingual Retrieval-Augmented Generation OK |
| a2505_15935 | 2505.15935 | MAPS: A Multilingual Benchmark for Agent Performance and Security OK |
| a2505_24195 | 2505.24195 | WikiGap: Promoting Epistemic Equity by Surfacing Knowledge Gaps Between English Wikipedia and other Language Editions OK |
| a2506_01615 | 2506.01615 | IndicRAGSuite: Large-Scale Datasets and a Benchmark for Indian Language RAG Systems OK |
| a2507_07543 | 2507.07543 | The Cross-Lingual Cost: Retrieval Biases in RAG over Arabic-English Corpora OK |
| a2507_22923 | 2507.22923 | How and Where to Translate? The Impact of Translation Strategies in Cross-lingual LLM Prompting OK |
| a2508_06600 | 2508.06600 | BrowseComp-Plus: A More Fair and Transparent Evaluation Benchmark of Deep-Research Agent OK |
| a2509_13930 | 2509.13930 | Linguistic Nepotism: Trading-off Quality for Language Preference in Multilingual RAG OK |
| a2510_15551 | 2510.15551 | Rethinking Cross-lingual Gaps from a Statistical Viewpoint OK |
| a2510_23070 | 2510.23070 | Quality-Aware Translation Tagging in Multilingual RAG system OK |
| a2511_09984 | 2511.09984 | Language Drift in Multilingual Retrieval-Augmented Generation: Characterization and Decoding-Time Mitigation OK |
| a2511_19324 | 2511.19324 | What Drives Cross-lingual Ranking? Retrieval Approaches with Multilingual Language Models OK |
| a2601_02956 | 2601.02956 | Enhancing Multilingual RAG Systems with Debiased Language Preference-Guided Query Fusion OK |
| a2601_05366 | 2601.05366 | Lost in Execution: On the Multilingual Robustness of Tool Calling in Large Language Models  |
| a2603_17070 | 2603.17070 | Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts OK |
| a2604_20199 | 2604.20199 | All Languages Matter: Understanding and Mitigating Language Bias in Multilingual RAG OK |
| a2604_24929 | 2604.24929 | GAIA-v2-LILT: Multilingual Adaptation of Agent Benchmark beyond Translation OK |
| a2604_25676 | 2604.25676 | CORAL: Adaptive Retrieval Loop for Culturally-Aligned Multilingual RAG OK |
| a2605_07249 | 2605.07249 | MLAIRE: Multilingual Language-Aware Information Retrieval Evaluation Protocal OK |
| a2605_29637 | 2605.29637 | Evaluating Cross-lingual Knowledge Consistency in Code-Mixed vis-a-vis Indian Languages using IndicKLAR OK |
| a2606_02404 | 2606.02404 | K-BrowseComp: A Web Browsing Agent Benchmark Grounded in Korean Contexts OK |
| a2606_15345 | 2606.15345 | Beyond Monolingual Deep Research: Evaluating Agents and Retrievers with Cross-Lingual BrowseComp-Plus OK |
| a2606_27595 | 2606.27595 | Ko-WideSearch: A Korean Breadth-Search Benchmark for Exhaustive Set Enumeration by Web Agents OK |
| a2608_01913 | 2608.01913 | Diagnosing Search Behavior and Failure Modes in Long-Horizon Search Agents OK |
| a2608_05212 | 2608.05212 | SearchAuditor: Auditing and Attributing Failures in Long-Horizon Search Agents OK |
| a2608_08775 | 2608.08775 | OmnilingualGAIA2: Evaluating the Multilingual Gap in Frontier AI Agents OK |
| a2608_15535 | 2608.15535 | L3Cube-IndicQuest v2: A Large-Scale Multilingual Benchmark for Evaluating Factual Knowledge of Large Language Models Across Indic Languages OK |
| a2609_00319 | 2609.00319 | Sources of Truth: A Multi-Platform, Multilingual Audit of Citations in AI Mental Health Information Queries OK |
| a2609_08094 | 2609.08094 | CIVI: A Framework for Diagnosing Search Agent Failures in Civic Information OK |
| a2609_19244 | 2609.19244 | Characterizing Web Search by Conversational LLM Agents: From Search Decisions and Strategies to Results and Responses OK |
| a2610_00606 | 2610.00606 | Where's Waldo? Query-language Preference under Cross-lingual Knowledge Disparities (recency sweep, arXiv API) OK |
| a2610_03574 | 2610.03574 | HyperBrowseComp: A Multilingual and Multimodal Stress Test for Web-Browsing Agents OK |
| benjamini1995bh |  | (manual entry)  |
| clark2020tydi |  | (manual entry)  |
| hecht2010tower |  | (manual entry)  |
| kale2026marathiweb |  | (manual entry)  |
| mast2026 |  | (manual entry)  |
| robertson2009bm25 |  | (manual entry)  |
| wikipediamonthly2026 |  | (manual entry)  |