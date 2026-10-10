#!/usr/bin/env python3
"""Resolve English Wikipedia titles -> Hindi/Telugu/Bengali/Tamil Wikipedia titles via Wikidata sitelinks.
Batched 50 titles per call, cached to corpus/meta/sitelinks.json. Polite: 1 call/sec."""
import json, sys, time, urllib.parse, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "corpus" / "meta" / "sitelinks.json"
UA = {"User-Agent": "indic-search-gap-research/0.1 (research; contact abraar@vizz.vizuara.ai)"}
SITES = ["hiwiki", "tewiki", "bnwiki", "tawiki"]

def load():
    return json.load(open(CACHE)) if CACHE.exists() else {}

def resolve(titles):
    cache = load()
    todo = [t for t in dict.fromkeys(titles) if t not in cache]
    print(f"{len(titles)} titles, {len(todo)} to resolve", flush=True)
    for i in range(0, len(todo), 50):
        batch = todo[i:i+50]
        q = urllib.parse.urlencode({"action": "wbgetentities", "sites": "enwiki", "titles": "|".join(batch),
                                    "props": "sitelinks", "format": "json"})
        url = "https://www.wikidata.org/w/api.php?" + q
        for attempt in range(5):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                    d = json.load(r)
                break
            except Exception as e:
                time.sleep(5 * (attempt + 1)); d = None
        if d is None:
            print("FAILED batch", i); continue
        norm = {n["from"]: n["to"] for n in d.get("normalized", [])}
        found = {}
        for qid, ent in d.get("entities", {}).items():
            sl = ent.get("sitelinks", {})
            en = sl.get("enwiki", {}).get("title")
            if en:
                found[en] = {"qid": qid, **{s: sl.get(s, {}).get("title") for s in SITES}}
        for t in batch:
            key = norm.get(t, t)
            cache[t] = found.get(key, {"qid": None, **{s: None for s in SITES}})
        json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=0)
        print(f"  {i+len(batch)}/{len(todo)}", flush=True)
        time.sleep(1.0)
    return cache

if __name__ == "__main__":
    titles = json.load(open(sys.argv[1]))
    resolve(titles)
