#!/usr/bin/env python3
"""Fetch full plain-text English Wikipedia articles for every item's English title (XorQA, MLQA)
and write them as extra English pool chunks: corpus/pools/en_extra.jsonl (ids "en:x<pageid>:<k>").
Polite: 20 titles per call, 1 call/sec, cached in corpus/raw/en_articles.json."""
import json, pathlib, time, urllib.parse, urllib.request, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_corpus import chunk_article
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "corpus" / "raw" / "en_articles.json"
UA = {"User-Agent": "indic-search-gap-research/0.1 (research; contact abraar@vizz.vizuara.ai)"}
items = json.load(open(ROOT / "corpus" / "items.json"))["items"]
titles = sorted({it["en_title"] for it in items if it.get("en_title")})
cache = {k: v for k, v in (json.load(open(CACHE)) if CACHE.exists() else {}).items() if v.get("text")}
todo = [t for t in titles if t not in cache]
print(len(titles), "titles,", len(todo), "to fetch")
for i in range(0, len(todo), 1):
    b = todo[i:i+1]
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "exlimit": 1,
                                "titles": "|".join(b), "redirects": 1, "format": "json"})
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers=UA), timeout=90)); break
        except Exception as e:
            time.sleep(5); d = None
    if not d: print("fail", i); continue
    rmap = {r["from"]: r["to"] for r in d["query"].get("redirects", [])}
    nmap = {n["from"]: n["to"] for n in d["query"].get("normalized", [])}
    pages = {p["title"]: p for p in d["query"]["pages"].values()}
    for t in b:
        t2 = rmap.get(nmap.get(t, t), nmap.get(t, t))
        p = pages.get(t2)
        cache[t] = {"pageid": p.get("pageid"), "title": t2, "text": p.get("extract", "")} if p and "missing" not in p else {"pageid": None, "title": t2, "text": ""}
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
    (print(f"  {i+len(b)}/{len(todo)}", flush=True) if (i % 50 == 0) else None)
    time.sleep(0.4)
n = 0
with open(ROOT / "corpus" / "pools" / "en_extra.jsonl", "w") as f:
    for t, a in cache.items():
        if not a["text"]: continue
        for k, c in enumerate(chunk_article(a["title"], a["text"])):
            f.write(json.dumps({"id": f"en:x{a['pageid']}:{k}", "lang": "en", "title": a["title"], "k": k, "text": c}, ensure_ascii=False) + "\n"); n += 1
print("en_extra chunks", n, "| articles with text", sum(1 for a in cache.values() if a["text"]), "/", len(cache))
