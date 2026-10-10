#!/usr/bin/env python3
"""Score answers: alias-aware exact/containment match in both scripts first; an LLM judge (a model
NOT under test) only where the string rule says WRONG and the answer is non-empty.

  python3 judge.py            -> results/judged/<model>.jsonl with fields: correct (0/1), how (string|llm|empty)
                                 and results/judge_cache.jsonl (one LLM verdict per unique (item, answer))
Judge model: google/gemini-2.5-flash (not in the experimental grid). Stage "judge".
"""
import concurrent.futures as cf
import glob
import hashlib
import json
import pathlib
import re
import sys
import threading
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cost_tracker  # noqa: E402
from agent import env, post  # noqa: E402
from prompts import SYSTEM_JUDGE, USER_JUDGE  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
JUDGED = ROOT / "results" / "judged"
CACHE = ROOT / "results" / "judge_cache.jsonl"
JUDGE_MODEL = "google/gemini-2.5-flash"
ITEMS = {it["id"]: it for it in json.load(open(ROOT / "corpus" / "items.json"))["items"]}
DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
TELU_DIGITS = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")


def norm(s):
    s = unicodedata.normalize("NFC", s or "").lower().translate(DEVA_DIGITS).translate(TELU_DIGITS)
    s = re.sub(r"[।॥.,;:!?\"'()\[\]{}«»“”‘’\-–—/]", " ", s)
    s = re.sub(r"\b(the|a|an)\b", " ", s)
    return " ".join(s.split())


def string_correct(answer, golds):
    a = norm(answer)
    if not a:
        return False
    for g in golds:
        g = norm(g)
        if not g:
            continue
        if a == g or (len(g) >= 2 and g in a and len(a) <= len(g) + 40):
            return True
        # numeric / year answers: compare digit strings
        da, dg = re.sub(r"\D", "", a), re.sub(r"\D", "", g)
        if dg and len(dg) >= 2 and da == dg:
            return True
    return False


_cache_lock = threading.Lock()


def load_cache():
    c = {}
    if CACHE.exists():
        for line in open(CACHE):
            r = json.loads(line)
            c[r["k"]] = r["verdict"]
    return c


def llm_judge(item, answer, key, cache, fout):
    k = hashlib.sha256(f"{item['id']}|{norm(answer)}".encode()).hexdigest()[:16]
    if k in cache:
        return cache[k]
    golds = " | ".join((item.get("ans_en") or []) + (item.get("ans_L") or []))
    body = {"model": JUDGE_MODEL, "temperature": 0, "max_tokens": 5, "reasoning": {"effort": "minimal"},
            "messages": [{"role": "system", "content": SYSTEM_JUDGE},
                         {"role": "user", "content": USER_JUDGE.format(q_en=item.get("q_en") or "-", q_L=item["q_L"], gold=golds, cand=answer[:300])}]}
    resp, _ = post(body, key)
    cost_tracker.log_call(JUDGE_MODEL, float(resp.get("usage", {}).get("cost", 0)), "judge")
    txt = (resp["choices"][0]["message"].get("content") or "").strip().upper()
    v = 1 if txt.startswith("CORRECT") else (-1 if txt.startswith("ABSTAIN") else 0)
    with _cache_lock:
        cache[k] = v
        fout.write(json.dumps({"k": k, "item": item["id"], "answer": answer[:300], "verdict": v}, ensure_ascii=False) + "\n")
        fout.flush()
    return v


def main():
    key = env("OPENROUTER_API_KEY")
    JUDGED.mkdir(exist_ok=True)
    cache = load_cache()
    fcache = open(CACHE, "a")
    clock = threading.Lock()
    for f in sorted(glob.glob(str(RAW / "*.jsonl"))):
        if "_discarded" in f:
            continue
        out = JUDGED / pathlib.Path(f).name
        done = set()
        if out.exists():
            done = {json.loads(l)["key"] for l in open(out)}
        recs = []
        for line in open(f):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r["key"] in done:
                continue
            done.add(r["key"])
            recs.append(r)
        fo = open(out, "a")
        n = {"llm": 0, "n": 0}

        def judge_one(r):
            it = ITEMS[r["item"]]
            golds = (it.get("ans_en") or []) + (it.get("ans_L") or [])
            ans = r.get("answer") or ""
            abstain = 0
            if not ans.strip():
                c, how = 0, "empty"
            elif string_correct(ans, golds):
                c, how = 1, "string"
            else:
                with clock:
                    cached = hashlib.sha256(f"{it['id']}|{norm(ans)}".encode()).hexdigest()[:16] in cache
                v = llm_judge(it, ans, key, cache, fcache) if cached else None
                if v is None:
                    try:
                        v = llm_judge(it, ans, key, cache, fcache)
                    except Exception as ex:
                        print("JUDGE FAIL", r["key"], str(ex)[:100], flush=True)
                        return None
                c, how = (1 if v == 1 else 0), "llm"
                abstain = int(v == -1)
                n["llm"] += 1
            return {"key": r["key"], "item": r["item"], "model": r["model"], "correct": c, "how": how, "abstain": abstain}

        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            for res in ex.map(judge_one, recs):
                if res is None:
                    continue
                with clock:
                    fo.write(json.dumps(res) + "\n")
                    fo.flush()
                    n["n"] += 1
        fo.close()
        print(f"{pathlib.Path(f).name}: judged {n['n']} new ({n['llm']} via LLM); spend ${cost_tracker.total():.3f}", flush=True)
    fcache.close()


if __name__ == "__main__":
    main()
