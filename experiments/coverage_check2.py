#!/usr/bin/env python3
"""Second, stronger verification of Indic coverage (stage "coverage2"): google/gemini-3.6-flash re-reads the
article for every item the first pass accepted (and for the audit sample's rejected items). Final
cov_L_verified = pass-1 yes AND pass-2 yes AND (string match OR a quoted sentence found in the article).
Output corpus/meta/coverage_llm2.jsonl; items.json updated in place."""
import json, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cost_tracker
from agent import env, post
from coverage_check import SYSTEM, USER, article_chunks, norm, ITEMS, POOLS, MAX_CHARS
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "corpus" / "meta" / "coverage_llm2.jsonl"
MODEL = "google/gemini-3.6-flash"
def main():
    key = env("OPENROUTER_API_KEY")
    data = json.load(open(ITEMS)); items = data["items"]
    audit_ids = {s["item"] for s in json.load(open(ROOT / "results" / "coverage_audit.json"))}
    done = {json.loads(l)["item"]: json.loads(l) for l in open(OUT)} if OUT.exists() else {}
    todo = [it for it in items if it["source"] == "xorqa_in" and it["cov_L_article"] and (it.get("cov_L_llm") or it["id"] in audit_ids) and it["id"] not in done]
    print(len(todo), "items for pass 2", flush=True)
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
        u = resp.get("usage", {}); cost_tracker.log_call(MODEL, float(u.get("cost", 0)), "coverage2")
        txt = (resp["choices"][0]["message"].get("content") or "").strip()
        yes = txt.upper() != "NONE" and len(txt) > 3
        found = None; gold = None
        if yes:
            nq = norm(txt)[:80]
            for c in cs:
                if nq and nq[:60] in norm(c["text"]):
                    found = True; gold = c; break
            if found is None: found = False
        rec = {"item": it["id"], "lang": it["lang"], "llm2_says_yes": yes, "quote2": txt[:400], "quote2_found": found,
               "gold_chunk_id2": gold["id"] if gold else None, "cost": float(u.get("cost", 0))}
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n"); fout.flush(); done[it["id"]] = rec
        if n % 50 == 0: print(f"  {n}/{len(todo)} ${cost_tracker.total():.3f}", flush=True)
    fout.close()
    agree = collections.Counter()
    for it in items:
        r = done.get(it["id"])
        if not r: continue
        it["cov_L_llm2"] = r["llm2_says_yes"]
        agree[(bool(it.get("cov_L_llm")), r["llm2_says_yes"])] += 1
        verified = bool(it.get("cov_L_llm")) and r["llm2_says_yes"] and (it["cov_L_answer"] or r["quote2_found"] or it.get("gold_L_chunk_id"))
        it["cov_L_verified"] = verified
        if it["source"] == "xorqa_in":
            it["factorial"] = verified
            if verified and not it.get("gold_L_chunk_id") and r["gold_chunk_id2"]:
                it["gold_L_chunk_id"] = r["gold_chunk_id2"]
                for c in chunks[it["lang"]].get(it["L_title"], []):
                    if c["id"] == r["gold_chunk_id2"]:
                        it["gold_L"] = c["text"].split("\n", 1)[1] if "\n" in c["text"] else c["text"]
    json.dump(data, open(ITEMS, "w"), ensure_ascii=False, indent=0)
    print("pass1 x pass2 agreement (llm1_yes, llm2_yes):", dict(agree))
    print("factorial-eligible now:", collections.Counter((i["lang"], i["source"]) for i in items if i.get("factorial")))
    print("spend", cost_tracker.total())
if __name__ == "__main__":
    main()
