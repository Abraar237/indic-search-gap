#!/usr/bin/env python3
"""Draw the judge audit sample: 40 judged agent answers (20 per language; per language 10 string-correct,
5 LLM-correct, 5 LLM-wrong/abstain), with the question, gold aliases and the answer, for manual labelling.
Writes results/audit_sample.json with manual_label = null; the labels are filled by hand."""
import glob, json, pathlib, random
ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEMS = {i["id"]: i for i in json.load(open(ROOT / "corpus" / "items.json"))["items"]}
J = {}
for f in glob.glob(str(ROOT / "results" / "judged" / "*.jsonl")):
    for l in open(f):
        r = json.loads(l); J[r["key"]] = r
R = {}
for f in glob.glob(str(ROOT / "results" / "raw" / "*.jsonl")):
    if "_discarded" in f: continue
    for l in open(f):
        r = json.loads(l)
        if r["key"] in J and r.get("grid") == "core": R[r["key"]] = r
rng = random.Random(23)
out = []
for lang in ("hi", "te"):
    pools = {"string_correct": [], "llm_correct": [], "llm_wrong": []}
    for k, r in R.items():
        if r["lang"] != lang: continue
        j = J[k]
        if j["how"] == "string" and j["correct"] == 1: pools["string_correct"].append(k)
        elif j["how"] == "llm" and j["correct"] == 1: pools["llm_correct"].append(k)
        elif j["how"] == "llm": pools["llm_wrong"].append(k)
    for grp, n in (("string_correct", 10), ("llm_correct", 5), ("llm_wrong", 5)):
        ks = pools[grp]; rng.shuffle(ks)
        for k in ks[:n]:
            r, j, it = R[k], J[k], ITEMS[R[k]["item"]]
            out.append({"key": k, "item": r["item"], "lang": lang, "model": r["model"], "qlang": r["qlang"], "policy": r["policy"], "pool": r["pool"],
                        "question": r["question"], "answer": r["answer"], "gold_en": it["ans_en"], "gold_L": it["ans_L"],
                        "judge": grp, "judge_correct": j["correct"], "judge_abstain": j.get("abstain", 0), "manual_label": None, "manual_note": ""})
json.dump(out, open(ROOT / "results" / "audit_sample.json", "w"), ensure_ascii=False, indent=1)
print("audit sample", len(out))
