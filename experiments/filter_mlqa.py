#!/usr/bin/env python3
"""Keep only MLQA questions that are self-contained (answerable as a standalone open-domain question,
i.e. they name their subject). Many MLQA questions presuppose the paragraph ("What did Keane often
request?"). Stage "filter". Writes corpus/meta/mlqa_selfcontained.json: {mlqa_id: {"ok": bool, "why": str}}."""
import json, pathlib, random, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cost_tracker
from agent import env, post
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw" / "mlqa" / "MLQA_V1" / "test"
OUT = ROOT / "corpus" / "meta" / "mlqa_selfcontained.json"
MODEL = "google/gemini-2.5-flash-lite"
SYSTEM = ("You judge whether a factual question is SELF-CONTAINED: a reader with no passage could understand exactly "
          "what is being asked and look the answer up, because the question names its subject (a person, place, work, "
          "organisation, event, or clearly specified concept). Questions that rely on an unstated passage ('he', 'the "
          "band', 'the committee', 'this method', 'what did Keane often request') are NOT self-contained. Also reject "
          "questions whose answer is a long explanation rather than a short fact. Reply with exactly one word: OK or NO.")
def flat(d):
    out = {}
    for a in d["data"]:
        for p in a["paragraphs"]:
            for q in p["qas"]:
                out[q["id"]] = {"title": a["title"], "q": q["question"], "ans": sorted({x["text"] for x in q["answers"]})}
    return out
H = flat(json.load(open(RAW / "test-context-hi-question-hi.json")))
E = flat(json.load(open(RAW / "test-context-en-question-en.json")))
ids = sorted(set(H) & set(E)); rng = random.Random(11); rng.shuffle(ids)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 450
done = json.load(open(OUT)) if OUT.exists() else {}
key = env("OPENROUTER_API_KEY")
for k in ids[:N]:
    if k in done: continue
    e = E[k]
    body = {"model": MODEL, "temperature": 0, "max_tokens": 5, "reasoning": {"effort": "minimal"},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": f"Question: {e['q']}\nGold answer: {' | '.join(e['ans'])}\n(The Wikipedia article it came from is titled \"{e['title']}\", but the reader does not see this.)\nSelf-contained?"}]}
    try:
        resp, _ = post(body, key)
    except Exception as ex:
        print("FAIL", k, str(ex)[:100]); continue
    cost_tracker.log_call(MODEL, float(resp.get("usage", {}).get("cost", 0)), "filter")
    txt = (resp["choices"][0]["message"].get("content") or "").strip().upper()
    done[k] = {"ok": txt.startswith("OK"), "q": e["q"], "title": e["title"]}
    if len(done) % 50 == 0:
        json.dump(done, open(OUT, "w"), ensure_ascii=False, indent=0); print(len(done), "ok so far", sum(1 for v in done.values() if v["ok"]), flush=True)
json.dump(done, open(OUT, "w"), ensure_ascii=False, indent=0)
print("checked", len(done), "self-contained", sum(1 for v in done.values() if v["ok"]), "spend", cost_tracker.total())
