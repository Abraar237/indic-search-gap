#!/usr/bin/env python3
"""LLM verification of Indic-Wikipedia coverage for XorQA items (stage "coverage").

For every XorQA item whose Indic article exists in the snapshot, ask a cheap model whether the
article states the answer to the question; return the supporting sentence or NONE. Used to
(a) rescue items where the answer is present but the string match failed (inflection, spelling,
numerals) and (b) catch false positives where the string occurs without answering the question.
The final coverage flag `cov_L_verified` = LLM says yes AND (string match OR the quoted sentence is
found in the article). Items gain `factorial` when verified; the quoted sentence's chunk becomes
gold_L. Output: corpus/meta/coverage_llm.jsonl; items.json updated in place.
"""
import json
import pathlib
import re
import sys
import time
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cost_tracker  # noqa: E402
from agent import env, post  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEMS = ROOT / "corpus" / "items.json"
POOLS = ROOT / "corpus" / "pools"
OUT = ROOT / "corpus" / "meta" / "coverage_llm.jsonl"
MODEL = "google/gemini-2.5-flash-lite"
MAX_CHARS = 14000

SYSTEM = ("You check whether a Wikipedia article (in Hindi or Telugu) contains the answer to a question. "
          "Read the article. If it states the answer (the same fact as the gold answer, possibly in a different "
          "script, spelling, inflection or numeral system), quote the single sentence from the article that "
          "states it, verbatim. If the article does not state the answer, reply exactly NONE.")
USER = ("Question (English): {q_en}\nQuestion ({lang}): {q_L}\nGold answer (English): {ans_en}\n"
        "Gold answer ({lang}): {ans_L}\n\nArticle:\n\"\"\"\n{article}\n\"\"\"\n\n"
        "Reply with the verbatim sentence that states the answer, or NONE.")


def norm(s):
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[।॥.,;:!?\"'()\[\]{}«»“”‘’\-–—/]", " ", s)
    return " ".join(s.split())


def article_chunks(lang, titles):
    want = set(titles)
    out = {}
    with open(POOLS / f"{lang}.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if r["title"] in want:
                out.setdefault(r["title"], []).append(r)
    return out


def main():
    key = env("OPENROUTER_API_KEY")
    data = json.load(open(ITEMS))
    items = data["items"]
    done = {}
    if OUT.exists():
        for line in open(OUT):
            r = json.loads(line)
            done[r["item"]] = r
    todo = [it for it in items if it["source"] == "xorqa_in" and it["cov_L_article"] and it["id"] not in done]
    print(f"{len(todo)} items to check; spend so far ${cost_tracker.total():.3f}", flush=True)
    chunks = {l: article_chunks(l, [it["L_title"] for it in items if it["lang"] == l and it.get("L_title")]) for l in ("hi", "te")}
    fout = open(OUT, "a")
    for n, it in enumerate(todo, 1):
        cs = sorted(chunks[it["lang"]].get(it["L_title"], []), key=lambda r: r["k"])
        article = "\n".join(c["text"].split("\n", 1)[1] if "\n" in c["text"] else c["text"] for c in cs)[:MAX_CHARS]
        body = {"model": MODEL, "temperature": 0, "max_tokens": 300, "reasoning": {"effort": "minimal"},
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": USER.format(q_en=it["q_en"], q_L=it["q_L"], lang={"hi": "Hindi", "te": "Telugu"}[it["lang"]],
                                                                     ans_en=" | ".join(it["ans_en"]), ans_L=" | ".join(it["ans_L"]) or "-", article=article)}]}
        try:
            resp, _ = post(body, key)
        except Exception as e:
            print("FAIL", it["id"], str(e)[:120]); continue
        u = resp.get("usage", {})
        cost_tracker.log_call(MODEL, float(u.get("cost", 0)), "coverage")
        txt = (resp["choices"][0]["message"].get("content") or "").strip()
        says_yes = txt.upper() != "NONE" and len(txt) > 3
        quoted_found = None
        gold_chunk = None
        if says_yes:
            nq = norm(txt)[:80]
            for c in cs:
                if nq and nq[:60] in norm(c["text"]):
                    quoted_found = True
                    gold_chunk = c
                    break
            if quoted_found is None:
                quoted_found = False
        rec = {"item": it["id"], "lang": it["lang"], "string_match": it["cov_L_answer"], "llm_says_yes": says_yes,
               "quote": txt[:400], "quote_found_in_article": quoted_found,
               "gold_chunk_id": gold_chunk["id"] if gold_chunk else None, "cost": float(u.get("cost", 0))}
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n"); fout.flush()
        done[it["id"]] = rec
        if n % 50 == 0:
            print(f"  {n}/{len(todo)} ${cost_tracker.total():.3f}", flush=True)
    fout.close()
    # fold back into items.json
    n_new = n_drop = 0
    for it in items:
        r = done.get(it["id"])
        if not r:
            continue
        verified = r["llm_says_yes"] and (it["cov_L_answer"] or r["quote_found_in_article"])  # string match recomputed from the current item
        it["cov_L_llm"] = r["llm_says_yes"]
        it["cov_L_verified"] = verified
        if verified and not it.get("factorial"):
            it["factorial"] = True
            n_new += 1
            if r["gold_chunk_id"]:
                it["gold_L_chunk_id"] = r["gold_chunk_id"]
                for c in chunks[it["lang"]].get(it["L_title"], []):
                    if c["id"] == r["gold_chunk_id"]:
                        it["gold_L"] = c["text"].split("\n", 1)[1] if "\n" in c["text"] else c["text"]
        if it.get("factorial") and it["source"] == "xorqa_in" and not verified:
            it["factorial"] = False
            it["factorial_dropped_by_llm"] = True
            n_drop += 1
    json.dump(data, open(ITEMS, "w"), ensure_ascii=False, indent=0)
    import collections
    print("added to factorial:", n_new, "| dropped (string match but LLM says no):", n_drop)
    print("factorial-eligible now:", collections.Counter((i["lang"], i["source"]) for i in items if i.get("factorial")))
    print("spend", cost_tracker.total())


if __name__ == "__main__":
    main()
