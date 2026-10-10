#!/usr/bin/env python3
"""Run the factorial grid. One episode at a time per pool (each BM25 pool is loaded once), items in
randomised order, resume-safe JSONL keyed by model|item|qlang|policy|pool|rep.

  python3 indic_runner.py --model google/gemini-2.5-flash-lite --grid core   [--limit 10] [--langs hi,te]
  python3 indic_runner.py --model ... --grid closed | oracle | none | noise | native_te
  python3 indic_runner.py --model ... --cells "L:free:both,L:dual:both" --items 60 [--retriever dense|bm25|hybrid]  (dense = bge-m3 is the main-grid retriever)

Grids (Q = question language, L = the item's Indic language; pools en | L | both; see EXPERIMENT_PLAN.md):
  core    : Q=L  x P{free,match,english,dual} x E{en,L,both}  +  Q=en x P{free,match} x E{en,L,both}
            (P=dual for Q=en only on E=L)                                  -> 19 cells
  closed  : no tool, Q in {en, L}
  oracle  : gold passage given; (Q=L, passage en), (Q=en, passage en), (Q=L, passage L when it exists)
  none    : Q=L, P=free, pool with the item's gold removed (hallucination / abstention floor), 50 items
  noise   : 30 items x 5 repeats of (Q=L, free, both)
  native_te: tydi_xor_rc items (natively written Telugu questions): Q=te x P{free,dual} x E{en,both}
Records -> results/raw/<model-slug>.jsonl
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import pathlib
import random
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cost_tracker  # noqa: E402
from agent import env, run_closed, run_episode, run_oracle  # noqa: E402
from index import make_searcher  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def pool_name(lang, e):
    return {"en": "en", "L": lang, "both": f"{lang}+en"}[e]


def eligible(items, langs, sources=("xorqa_in", "mlqa")):
    """Items used in the controlled factorial: gold evidence exists in BOTH languages."""
    return [it for it in items if it["lang"] in langs and it["source"] in sources and it.get("factorial")]


def build_jobs(args, items):
    langs = args.langs.split(",")
    jobs = []
    if args.grid == "core":
        pool_items = eligible(items, langs)
        if args.items:
            pool_items = select(pool_items, args.items, langs)
        cells = []
        for p in ("free", "match", "english", "dual"):
            for e in ("en", "L", "both"):
                cells.append(("L", p, e))
        for p in ("free", "match"):
            for e in ("en", "L", "both"):
                cells.append(("en", p, e))
        cells.append(("en", "dual", "L"))
        if args.cells:
            cells = [tuple(c.split(":")) for c in args.cells.split(",")]
        for it in pool_items:
            for q, p, e in cells:
                jobs.append(("episode", it, q, p, e, 0))
    elif args.grid == "closed":
        for it in select(eligible(items, langs), args.items, langs) if args.items else eligible(items, langs):
            for q in ("en", "L"):
                jobs.append(("closed", it, q, None, None, 0))
    elif args.grid == "oracle":
        for it in select(eligible(items, langs), args.items, langs) if args.items else eligible(items, langs):
            jobs.append(("oracle", it, "L", "en", None, 0))
            jobs.append(("oracle", it, "en", "en", None, 0))
            if it.get("gold_L"):
                jobs.append(("oracle", it, "L", "L", None, 0))
    elif args.grid == "noise":
        pool_items = select(eligible(items, langs), 30, langs)
        for it in pool_items:
            for rep in range(1, 6):
                jobs.append(("episode", it, "L", "free", "both", rep))
    elif args.grid == "native_te":
        nat = [it for it in items if it["source"] == "tydi_xor_rc"]
        if args.items:
            nat = nat[: args.items]
        for it in nat:
            for p in ("free", "dual"):
                for e in ("en", "both"):
                    jobs.append(("episode", it, "L", p, e, 0))
    elif args.grid == "none":
        pool_items = select(eligible(items, langs), 50, langs)
        for it in pool_items:
            jobs.append(("episode", it, "L", "free", "none", 0))
    return jobs


def select(items, n, langs):
    """Deterministic per-language sample of n items each, stratified by source."""
    out = []
    for lang in langs:
        li = [it for it in items if it["lang"] == lang]
        rng = random.Random(3)
        rng.shuffle(li)
        out += li[:n]
    return out


def key_of(model, job, retriever="hybrid"):
    kind, it, q, p, e, rep = job
    tag = "" if (retriever == "dense" or kind != "episode") else f"|{retriever}"
    return hashlib.sha256(f"{model}|{kind}|{it['id']}|{q}|{p}|{e}|{rep}{tag}".encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--grid", default="core")
    ap.add_argument("--langs", default="hi,te")
    ap.add_argument("--items", type=int, default=0, help="items per language (0 = all eligible)")
    ap.add_argument("--cells", default="")
    ap.add_argument("--limit", type=int, default=0, help="cap on total jobs (pilot)")
    ap.add_argument("--reasoning", default="minimal")
    ap.add_argument("--stage", default="")
    ap.add_argument("--retriever", default="dense", choices=["hybrid", "bm25", "dense"])
    ap.add_argument("--workers", type=int, default=8, help="concurrent episodes (retrieval is serialised by a lock)")
    args = ap.parse_args()
    key = env("OPENROUTER_API_KEY")
    items = json.load(open(ROOT / "corpus" / "items.json"))["items"]
    jobs = build_jobs(args, items)
    rng = random.Random(11)
    rng.shuffle(jobs)
    if args.limit:
        jobs = jobs[: args.limit]
    slug = args.model.replace("/", "_")
    # one file per (model, retriever) so two runners never append to the same file
    out_path = RAW / (f"{slug}.jsonl" if args.retriever == "dense" or args.grid in ("closed", "oracle") else f"{slug}__{args.retriever}.jsonl")
    done = set()
    if out_path.exists():
        for line in open(out_path):
            done.add(json.loads(line)["key"])
    todo = [j for j in jobs if key_of(args.model, j, args.retriever) not in done]
    print(f"{args.model} grid={args.grid}: {len(jobs)} jobs, {len(todo)} to do, spend so far ${cost_tracker.total():.3f}", flush=True)
    # group by pool so each BM25 index is loaded once
    by_pool = {}
    for j in todo:
        kind, it, q, p, e, rep = j
        pn = None if kind != "episode" else ("none:" + it["lang"] if e == "none" else pool_name(it["lang"], e))
        by_pool.setdefault(pn, []).append(j)
    fout = open(out_path, "a")
    stage = args.stage or args.grid
    wlock = threading.Lock()
    prog = {"n": 0, "stop": False}
    for pn, js in by_pool.items():
        if not args.model.startswith("modal/"):
            rem = cost_tracker.remaining_credit()
            if rem is not None and rem < 3.0:
                print(f"STOP: shared OpenRouter credit remaining ${rem:.2f} < $3; refusing to start pool {pn}", flush=True)
                break
            print(f"pool {pn}: {len(js)} jobs; shared key remaining ${rem}", flush=True)
        searcher = None
        if pn:
            real = pn.split(":")[1] + "+en" if pn.startswith("none:") else pn
            searcher = LockedSearcher(make_searcher(real, args.retriever))

        def work(j):
            if prog["stop"]:
                return
            kind, it, q, p, e, rep = j
            qlang = it["lang"] if q == "L" else "en"
            try:
                if kind == "episode":
                    if e == "none":
                        rec = run_episode(args.model, it, qlang, p, "none", GoldFree(searcher, it), key, args.reasoning, stage)
                    else:
                        rec = run_episode(args.model, it, qlang, p, pn, searcher, key, args.reasoning, stage)
                elif kind == "closed":
                    rec = run_closed(args.model, it, qlang, key, args.reasoning, stage)
                else:
                    rec = run_oracle(args.model, it, qlang, p, key, args.reasoning, stage)
            except cost_tracker.CostCapExceeded as ex:
                print("HARD STOP:", ex, flush=True)
                prog["stop"] = True
                return
            except Exception as ex:
                print("FAIL", it["id"], q, p, e, str(ex)[:200], flush=True)
                time.sleep(2)
                return
            rec["key"] = key_of(args.model, j, args.retriever)
            rec["rep"] = rep
            rec["grid"] = args.grid
            rec["retriever"] = args.retriever if kind == "episode" else None
            with wlock:
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                prog["n"] += 1
                if prog["n"] % 50 == 0:
                    print(f"  {prog['n']}/{len(todo)} ${cost_tracker.total():.3f}", flush=True)

        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            list(ex.map(work, js))
        if prog["stop"]:
            break
        del searcher
    fout.close()
    print("done; spend", cost_tracker.total())


class LockedSearcher:
    """Serialises retrieval (torch MPS matmul + bge-m3 encode are not guaranteed thread-safe); LLM calls run in parallel."""

    def __init__(self, inner):
        self.inner = inner
        self.lock = threading.Lock()

    def search(self, q, k, exclude_ids=()):
        with self.lock:
            return self.inner.search(q, k, exclude_ids)


class GoldFree:
    """Searcher wrapper that hides the item's gold evidence (E = NONE)."""

    def __init__(self, searcher, item):
        self.s = searcher
        self.item = item

    def search(self, q, k):
        from agent import is_gold_hit
        hits = self.s.search(q, k + 10)
        return [h for h in hits if not is_gold_hit(h, self.item)][:k]


if __name__ == "__main__":
    main()
