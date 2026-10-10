#!/usr/bin/env python3
"""Verify every arXiv ID cited in lit_review/00_preemption_sweep_2026-10-10.md
against the arXiv API and write lit_review/lit_review.csv.

Usage:  python3 lit_review/verify_refs.py

Columns: arxiv_id, title, first_authors, year_month, category, angle,
         nickname_in_sweep, verified (OK / TITLE_MISMATCH / NOT_FOUND)

Angle and nickname come from META below, which was built by hand from the
section in which each ID appears in the sweep (sec 1 benchmarks, sec 2 mRAG,
sec 3 agents, sec 4 query language, sec 5 knowledge/corpus gaps). The third
field of META is a case-insensitive regex that the fetched title must match
for the row to count as OK; otherwise it is TITLE_MISMATCH and must be checked
by hand. Nothing here invents metadata: if the API and the abs page both fail
the row is NOT_FOUND with empty title/authors.
"""
import csv
import html
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWEEP = HERE / "00_preemption_sweep_2026-10-10.md"
OUT = HERE / "lit_review.csv"

# Regex matches that are not arXiv IDs (DOI fragments etc.)
NOT_ARXIV = {"5712.38085"}  # tail of DOI 10.1145/3805712.3808534 (MarathiWeb)

# id -> (angle, nickname_in_sweep, title_regex)
META = {
    # ---- sec 1a retrieval benchmarks
    "2210.09984": ("benchmark-indic", "MIRACL", r"miracl"),
    "2108.13897": ("benchmark-indic", "mMARCO", r"mmarco"),
    "2312.09508": ("benchmark-indic", "IndicIRSuite / INDIC-MARCO", r"indic"),
    "2408.09437": ("benchmark-indic", "Hindi-BEIR", r"hindi"),
    "2409.05401": ("benchmark-indic", "Hindi-BEIR (companion)", r"hindi"),
    "2402.03216": ("benchmark-indic", "MLDR / BGE-M3", r"m3|multi-?linguality|multi-?granularity"),
    "2502.13595": ("benchmark-multilingual", "MMTEB / MTEB(Indic)", r"mmteb|text embedding"),
    "2506.01615": ("benchmark-indic", "IndicRAGSuite / IndicMSMarco", r"indic"),
    "2501.19264": ("benchmark-multilingual", "mFollowIR", r"followir|instruction"),
    "2304.12367": ("benchmark-multilingual", "NeuCLIR 2022", r"neuclir"),
    "2404.08071": ("benchmark-multilingual", "NeuCLIR 2023", r"neuclir"),
    "2509.14355": ("benchmark-multilingual", "NeuCLIR 2024", r"neuclir"),
    # ---- sec 1b open-domain / cross-lingual QA
    "2010.11856": ("benchmark-indic", "XOR-TyDi QA", r"xor"),
    "2007.15207": ("benchmark-multilingual", "MKQA", r"mkqa"),
    "1910.07475": ("benchmark-indic", "MLQA", r"mlqa"),
    "1910.11856": ("benchmark-indic", "XQuAD", r"cross-lingual transferability|xquad"),
    "2308.16884": ("benchmark-indic", "Belebele", r"belebele"),
    "2305.11938": ("benchmark-indic", "XTREME-UP", r"xtreme"),
    "2305.06897": ("benchmark-multilingual", "AfriQA", r"afriqa"),
    "2410.13716": ("benchmark-indic", "MIRAGE-Bench", r"mirage"),
    "2410.01171": ("benchmark-multilingual", "BordIRlines", r"bordirlines|culturally"),
    "2408.10151": ("benchmark-indic", "MLNeedle", r"needle|haystack"),
    "2505.10089": ("query-language", "XRAG", r"xrag|cross-lingual retrieval-augmented"),
    # ---- sec 1c Indic LLM evaluation suites
    "2212.05409": ("benchmark-indic", "IndicXTREME / IndicQA / IndicCorp v2", r"indic"),
    "2404.16816": ("benchmark-indic", "IndicGenBench", r"indicgenbench|indic"),
    "2407.13522": ("benchmark-indic", "Indic QA Benchmark", r"indic"),
    "2411.02538": ("benchmark-indic", "MILU", r"milu"),
    "2501.15747": ("benchmark-indic", "IndicMMLU-Pro", r"indicmmlu|indic"),
    "2406.15053": ("benchmark-indic", "Pariksha", r"pariksha"),
    "2409.08706": ("benchmark-indic", "L3Cube-IndicQuest v1", r"indicquest|indic"),
    "2608.15535": ("knowledge-gap", "L3Cube-IndicQuest v2", r"indicquest|indic"),
    "2505.03688": ("benchmark-indic", "IndicSQuAD", r"indicsquad|squad|indic"),
    "2412.03304": ("benchmark-multilingual", "Global-MMLU", r"global[- ]mmlu"),
    "2411.19799": ("benchmark-multilingual", "INCLUDE", r"include"),
    "2504.10356": ("knowledge-gap", "MultiLoKo", r"multiloko"),
    "2502.21228": ("knowledge-gap", "ECLeKTic", r"eclektic"),
    "2502.09642": ("benchmark-indic", "Krutrim-2 (BharatBench ref)", r"krutrim"),
    "2410.13671": ("benchmark-indic", "Health-Pariksha", r"health|pariksha"),
    "2510.25409": ("benchmark-indic", "BhashaBench V1", r"bhasha"),
    "2508.16185": ("benchmark-indic", "ParamBench", r"param"),
    "2512.00333": ("benchmark-indic", "IndicParam", r"indic|param"),
    "2602.22125": ("benchmark-indic", "IndicIFEval", r"indic|ifeval|instruction"),
    "2512.01852": ("benchmark-indic", "BHRAM-IL", r"bhram|hallucination|indic"),
    "2605.29637": ("knowledge-gap", "IndicKLAR", r"indic|klar"),
    "2509.21294": ("corpus-coverage", "Updesh", r"updesh"),
    "2403.06350": ("corpus-coverage", "Sangraha / IndicLLMSuite", r"indicllmsuite|indic|sangraha"),
    # ---- sec 1d 2025-26 Indic RAG resources
    "2508.19831": ("benchmark-indic", "ChatRAG-Hi", r"hindi|chatrag|conversational"),
    "2608.14886": ("benchmark-indic", "AgriTrust-RAG", r"agri|bengali|bangla"),
    "2608.28645": ("benchmark-indic", "Tulu legal RAG", r"tulu|legal|kannada"),
    "2601.10205": ("benchmark-indic", "Persona-instruction retrieval (12 Indian langs)", r"persona|indian|indic"),
    "2502.17163": ("benchmark-multilingual", "MEMERAG", r"memerag|meta-evaluation"),
    "2512.05959": ("benchmark-multilingual", "M4-RAG", r"m4|multimodal|multilingual"),
    # ---- sec 2 multilingual RAG analyses
    "2502.11175": ("multilingual-rag", "Park & Lee MLRS / DKM-RAG", r"language preference"),
    "2601.02956": ("multilingual-rag", "DeLP / DELTA", r"language preference|query fusion"),
    "2604.20199": ("multilingual-rag", "LAURA", r"all languages matter|language bias"),
    "2410.21970": ("multilingual-rag", "Futurepedia", r"not all languages are equal"),
    "2504.03616": ("multilingual-rag", "tRAG / MultiRAG / CrossRAG", r"multilingual retrieval-augmented|knowledge-intensive"),
    "2504.00597": ("multilingual-rag", "Qi et al. consistency of context utilization", r"consisten|context utilization"),
    "2507.07543": ("multilingual-rag", "Cross-Lingual Cost (Amiraz)", r"cross-lingual cost|arabic"),
    "2510.23070": ("multilingual-rag", "QTT-RAG", r"translation tagging|quality"),
    "2511.09984": ("multilingual-rag", "Language Drift / SCD", r"language drift"),
    "2604.25676": ("multilingual-rag", "CORAL", r"coral|cultural"),
    "2507.22923": ("query-language", "How and Where to Translate? (Gupta)", r"translat"),
    "2510.00908": ("multilingual-rag", "CLIR survey (Goworek)", r"bridging language gaps|cross-lingual"),
    "2511.19324": ("multilingual-rag", "What Drives Cross-lingual Ranking?", r"cross-lingual|ranking"),
    "2603.04238": ("multilingual-rag", "Retrieval or Representation? (Asenov)", r"retrieval or representation"),
    "2408.11942": ("multilingual-rag", "Wu, Ren, Verberne limits of CL-DPR", r"dense passage retrieval|low-resource|cross-lingual"),
    "2305.14332": ("multilingual-rag", "Muller et al. attribution", r"attribution"),
    "2608.05163": ("multilingual-rag", "Privacy stage-decomposed audit (Li, Fan, Zhuang)", r"privacy"),
    "2604.14896": ("multilingual-rag", "Agentic RAG for Ukrainian", r"ukrainian"),
    "2509.13930": ("multilingual-rag", "Linguistic Nepotism", r"nepotism"),
    "2407.05502": ("multilingual-rag", "Faux Polyglot", r"faux polyglot"),
    "2407.01463": ("multilingual-rag", "Chirkova et al. RAG in multilingual settings", r"multilingual"),
    "2605.07249": ("multilingual-rag", "MLAIRE", r"mlaire|language-aware"),
    "2511.19325": ("multilingual-rag", "Generative Query Expansion for CLIR", r"query expansion"),
    "2601.04768": ("multilingual-rag", "LangSAE Editing", r"sparse autoencoder|language|embedding"),
    "2601.14896": ("multilingual-rag", "LcRL", r"language-coupled|reinforcement"),
    "2604.25182": ("multilingual-rag", "CroSearch-R1", r"crosearch|cross-lingual search"),
    "2607.02966": ("multilingual-rag", "TR-RAG", r"rag|cross-lingual|translat|retrieval"),
    "2608.27481": ("multilingual-rag", "XHotpotQA", r"hotpot"),
    # ---- sec 3 search agents
    "2504.19314": ("agentic-search", "BrowseComp-ZH", r"browsecomp-?zh|chinese"),
    "2606.02404": ("agentic-search", "K-BrowseComp", r"k-?browsecomp|korean"),
    "2606.27595": ("agentic-search", "Ko-WideSearch", r"widesearch|korean"),
    "2508.07999": ("agentic-search", "WideSearch", r"widesearch"),
    "2501.07572": ("agentic-search", "WebWalkerQA", r"webwalker"),
    "2510.24701": ("agentic-search", "Tongyi DeepResearch", r"tongyi|deep ?research"),
    "2610.03574": ("agentic-search", "HyperBrowseComp", r"hyperbrowsecomp|browsecomp"),
    "2606.15345": ("agentic-search", "XBCP", r"browsecomp|cross-lingual"),
    "2508.06600": ("agentic-search", "BrowseComp-Plus", r"browsecomp"),
    "2505.15935": ("agentic-search", "MAPS", r"\bmaps\b"),
    "2604.24929": ("agentic-search", "GAIA-v2-LILT", r"gaia|translat|locali"),
    "2608.08775": ("agentic-search", "OmnilingualGAIA2", r"omnilingual|gaia"),
    "2608.03735": ("agentic-search", "TART (Pahuja)", r"planning failures|multilingual"),
    "2609.23490": ("agentic-search", "BabelArena", r"babel"),
    "2607.06008": ("agentic-search", "PolyWorkBench", r"polywork|cross-lingual|workflow"),
    "2506.05334": ("agentic-search", "Search Arena", r"search arena"),
    "2609.19244": ("agentic-search", "Characterizing Web Search by Conversational LLM Agents (Amani)", r"web search|conversational"),
    "2609.00319": ("agentic-search", "Sources of Truth", r"sources|citation"),
    "2608.30052": ("agentic-search", "Query language selects the market (Zatuchin)", r"market|language|generative search"),
    "2608.01913": ("agentic-search", "Diagnosing Search Behavior and Failure Modes (Liu, Mao, Zhu, Chua)", r"search|failure"),
    "2608.05212": ("agentic-search", "SearchAuditor", r"searchauditor|audit|search"),
    "2609.08094": ("agentic-search", "CIVI / ARISE", r"civi|arise|civic"),
    "2505.19253": ("agentic-search", "DeepResearchGym", r"deepresearchgym|deep research"),
    "2604.17632": ("agentic-search", "Code-Switching IR (Zeng, Lu)", r"code-?switch"),
    "2606.30790": ("agentic-search", "Indi-RomCoM", r"roman|indic|code-?mix"),
    "2510.07978": ("agentic-search", "VoiceAgentBench", r"voiceagent|voice"),
    # NOTE: the sweep assigns 2603.05515 to "Lost in Execution" and 2601.05366 to
    # ITC; the arXiv API returns the opposite (the two IDs are swapped in the
    # sweep), so both rows are expected to come out TITLE_MISMATCH.
    "2603.05515": ("agentic-search", "Lost in Execution / MLCL", r"lost in execution|multilingual robustness"),
    "2601.05366": ("agentic-search", "ITC", r"international tool calling"),
    "2506.23394": ("agentic-search", "TUCAN", r"tucan|bulgarian|language of tools"),
    "2404.09992": ("agentic-search", "MMInA", r"mmina|multihop|multimodal"),
    "2409.12959": ("agentic-search", "MMSearch", r"mmsearch"),
    "2506.20670": ("agentic-search", "MMSearch-R1", r"mmsearch"),
    # ---- sec 4 query / reasoning language
    "2403.10258": ("query-language", "Is Translation All You Need? (Liu)", r"translation all you need"),
    "2308.01223": ("query-language", "self-translate (Etxaniz)", r"think better in english|self-translat"),
    "2402.10588": ("query-language", "Do Llamas Work in English? (Wendler)", r"llamas"),
    "2502.15603": ("query-language", "Do Multilingual LLMs Think in English? (Schut)", r"think in english"),
    "2406.20052": ("query-language", "Language Confusion (Marchisio)", r"language confusion"),
    "2510.07300": ("query-language", "M-Thinker", r"m-?thinker|multilingual reasoning"),
    "2606.01464": ("query-language", "Cross-lingual self-consistency (Elhady)", r"consisten|cross-lingual"),
    "2509.23659": ("query-language", "Agarwal et al. enterprise consistency", r"consisten|multilingual|enterprise"),
    # ---- sec 5c language-dependent factual recall
    "2010.06189": ("knowledge-gap", "X-FACTR", r"x-factr|factual"),
    "2102.00894": ("knowledge-gap", "mLAMA", r"multilingual lama|mlama|factual knowledge"),
    "2203.11552": ("knowledge-gap", "mParaRel", r"factual consistency|multilingual"),
    "2310.10378": ("knowledge-gap", "RankC / BMLAMA", r"cross-lingual consistency|factual"),
    "2305.13675": ("knowledge-gap", "Polyglot or Not?", r"polyglot"),
    "2406.16135": ("knowledge-gap", "Crosslingual Capabilities and Knowledge Barriers (Chua)", r"knowledge barriers|crosslingual"),
    "2404.11553": ("knowledge-gap", "Language Ranker", r"language ranker"),
    "2404.04990": ("knowledge-gap", "MLaKE", r"mlake|knowledge editing"),
    "2410.14387": ("knowledge-gap", "How Do Multilingual LMs Remember Facts? (Fierro)", r"remember|facts"),
    "2504.04264": ("knowledge-gap", "Lost in Multilinguality / KLAR", r"lost in multilinguality|knowledge"),
    "2504.20022": ("knowledge-gap", "Better To Ask in English? (Rohera)", r"ask in english|english"),
    "2505.14824": ("knowledge-gap", "Tracing Multilingual Factual Knowledge Acquisition (Liu)", r"tracing|factual knowledge"),
    "2505.20546": ("knowledge-gap", "Paths Not Taken", r"paths not taken"),
    "2510.10280": ("knowledge-gap", "Entity-Level Alignment (Liu, Wang, Yvon, Schuetze)", r"entity|consisten"),
    "2510.15551": ("knowledge-gap", "Rethinking Cross-lingual Gaps, Statistical Viewpoint (Piratla)", r"cross-lingual gaps|statistical"),
    "2603.17070": ("knowledge-gap", "LRMs Struggle to Transfer Parametric Knowledge Across Scripts (Bandarkar)", r"script|parametric knowledge"),
    "2606.06586": ("knowledge-gap", "PolyFact", r"polyfact|facts"),
    "2606.24579": ("knowledge-gap", "Cross-Lingual Exploration for Parametric Knowledge (Diskind)", r"parametric knowledge|cross-lingual"),
    "2609.09349": ("knowledge-gap", "SWORD", r"sword|false|wikidata"),
    # ---- sec 5d Wikipedia/Wikidata coverage
    "2505.24195": ("knowledge-gap", "WikiGap", r"wikigap|gap"),
    "2609.22375": ("knowledge-gap", "Kronk, Bias in Coverage of Humans in Wikidata", r"wikidata|bias|humans"),
    "2406.09948": ("knowledge-gap", "BLEnD", r"blend"),
    "2508.16139": ("knowledge-gap", "XLQA", r"xlqa|locale"),
    "2604.00019": ("knowledge-gap", "RiDiC", r"ridic|popularity|entity"),
    # ---- sec 5b web text
    "2506.20920": ("corpus-coverage", "FineWeb-2", r"fineweb"),
}

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
UA = "indic-search-gap-litreview/1.0 (mailto:hello@viz-vm4.com)"


def extract_ids(text):
    ids = []
    for m in re.finditer(r"\d{4}\.\d{4,5}", text):
        s = m.group(0)
        if s in NOT_ARXIV or s in ids:
            continue
        ids.append(s)
    return ids


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def fetch_with_retry(url):
    for attempt in range(4):
        try:
            return http_get(url)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  429 from arXiv; sleeping 30 s (attempt {attempt+1})", file=sys.stderr)
                time.sleep(30)
                continue
            if e.code == 404:
                return None
            print(f"  HTTP {e.code} for {url}", file=sys.stderr)
            time.sleep(5)
        except Exception as e:  # network blips
            print(f"  error {e!r} for {url}", file=sys.stderr)
            time.sleep(5)
    return None


def fmt_authors(names):
    names = [n for n in names if n]
    if len(names) > 3:
        return "; ".join(names[:3]) + " et al."
    return "; ".join(names)


def parse_api(xml_text):
    """Return dict id -> record from an Atom feed."""
    out = {}
    root = ET.fromstring(xml_text)
    for e in root.findall("a:entry", NS):
        idurl = e.findtext("a:id", default="", namespaces=NS)
        m = re.search(r"abs/(\d{4}\.\d{4,5})", idurl)
        if not m:
            continue  # the API emits an error entry for unknown ids
        title = re.sub(r"\s+", " ", e.findtext("a:title", default="", namespaces=NS)).strip()
        authors = [a.findtext("a:name", default="", namespaces=NS) for a in e.findall("a:author", NS)]
        published = e.findtext("a:published", default="", namespaces=NS)[:7]
        prim = e.find("arxiv:primary_category", NS)
        cat = prim.get("term") if prim is not None else ""
        out[m.group(1)] = dict(title=title, first_authors=fmt_authors(authors),
                               year_month=published, category=cat)
    return out


def parse_abs(html_text):
    def meta(name):
        m = re.search(r'<meta\s+name="%s"\s+content="([^"]*)"' % re.escape(name), html_text)
        return html.unescape(m.group(1)).strip() if m else ""
    title = re.sub(r"\s+", " ", meta("citation_title"))
    if not title:
        return None
    authors = [html.unescape(a) for a in re.findall(r'<meta\s+name="citation_author"\s+content="([^"]*)"', html_text)]
    date = meta("citation_date")  # YYYY/MM/DD
    ym = date[:7].replace("/", "-")
    m = re.search(r'<span class="primary-subject">([^<]*)</span>', html_text)
    cat = ""
    if m:
        mm = re.search(r"\(([^)]+)\)", m.group(1))
        cat = mm.group(1) if mm else m.group(1)
    return dict(title=title, first_authors=fmt_authors(authors), year_month=ym, category=cat)


def main():
    text = SWEEP.read_text(encoding="utf-8")
    ids = extract_ids(text)
    missing_meta = [i for i in ids if i not in META]
    extra_meta = [i for i in META if i not in ids]
    if missing_meta or extra_meta:
        print("META out of sync with sweep.\n  missing:", missing_meta, "\n  extra:", extra_meta, file=sys.stderr)
        sys.exit(1)
    print(f"{len(ids)} unique arXiv ids extracted (excluded non-arXiv matches: {sorted(NOT_ARXIV)})")

    records = {}
    for b in range(0, len(ids), 50):
        batch = ids[b:b + 50]
        url = API + "?" + urllib.parse.urlencode({"id_list": ",".join(batch), "max_results": len(batch)})
        print(f"API batch {b//50+1}: {len(batch)} ids")
        xml_text = fetch_with_retry(url)
        if xml_text:
            try:
                records.update(parse_api(xml_text))
            except ET.ParseError as e:
                print(f"  XML parse error: {e}", file=sys.stderr)
        if b + 50 < len(ids):
            time.sleep(3.5)

    failures = [i for i in ids if i not in records]
    print(f"API returned {len(records)}/{len(ids)}; falling back to abs pages for {len(failures)}")
    for i in failures:
        time.sleep(3.0)
        page = fetch_with_retry(f"https://arxiv.org/abs/{i}")
        rec = parse_abs(page) if page else None
        if rec:
            records[i] = rec
            print(f"  abs fallback OK: {i}")
        else:
            print(f"  NOT_FOUND: {i}")

    rows = []
    counts = {"OK": 0, "TITLE_MISMATCH": 0, "NOT_FOUND": 0}
    for i in ids:
        angle, nick, pat = META[i]
        rec = records.get(i)
        if not rec:
            status = "NOT_FOUND"
            rec = dict(title="", first_authors="", year_month="", category="")
        elif re.search(pat, rec["title"], re.I):
            status = "OK"
        else:
            status = "TITLE_MISMATCH"
        counts[status] += 1
        rows.append(dict(arxiv_id=i, title=rec["title"], first_authors=rec["first_authors"],
                         year_month=rec["year_month"], category=rec["category"], angle=angle,
                         nickname_in_sweep=nick, verified=status))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["arxiv_id", "title", "first_authors", "year_month", "category",
                                          "angle", "nickname_in_sweep", "verified"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT} ({len(rows)} rows): {counts}")
    for r in rows:
        if r["verified"] != "OK":
            print(f"  {r['verified']:15s} {r['arxiv_id']}  sweep='{r['nickname_in_sweep']}'  fetched='{r['title']}'")


if __name__ == "__main__":
    main()
