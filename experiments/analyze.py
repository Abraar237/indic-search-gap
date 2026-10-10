#!/usr/bin/env python3
"""Single analysis pass: results/raw/*.jsonl + results/judged/*.jsonl + corpus/items.json
-> results/analysis.json. Every number in the paper traces to this file. Seeded; byte-identical.

Usage: python3 analyze.py
"""
import glob
import json
import os
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "results", "raw")
JUDGED = os.path.join(ROOT, "results", "judged")
OUT = os.path.join(ROOT, "results", "analysis.json")
RNG = np.random.default_rng(42)
N_BOOT = 10_000
N_PERM = 20_000
N_PERM_INTER = 5_000
ITEMS = {it["id"]: it for it in json.load(open(os.path.join(ROOT, "corpus", "items.json")))["items"]}
LATIN = {"Latn"}


# ---------- loading ----------
def load():
    judged = {}
    for f in glob.glob(os.path.join(JUDGED, "*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            judged[r["key"]] = r
    rows = []
    seen = set()
    for f in sorted(glob.glob(os.path.join(RAW, "*.jsonl"))):
        if "_discarded" in f:
            continue
        for line in open(f):
            try:
                r = json.loads(line)
            except Exception:
                continue  # a torn line from a concurrent append; the key is simply re-run on resume
            if r["key"] in seen:
                continue  # duplicate from an overlapping run
            seen.add(r["key"])
            j = judged.get(r["key"])
            if j is None:
                continue
            s = r.get("searches") or []
            it = ITEMS.get(r["item"], {})
            if r.get("grid") not in ("native_te", "uncovered") and not it.get("factorial"):
                continue  # only items whose evidence exists in both languages enter the controlled analysis
            rows.append({
                "retriever": r.get("retriever") or "dense", "abstain": int(j.get("abstain", 0)),
                "key": r["key"], "model": r["model"], "item": r["item"], "lang": r["lang"], "source": r["source"],
                "qlang": "L" if r["qlang"] != "en" else "en", "policy": r["policy"], "pool": r["pool"],
                "E": ("closed" if r["policy"] == "closed" else pool_to_E(r["pool"], r["lang"])), "rep": r.get("rep", 0), "grid": r.get("grid"),
                "native": int(r.get("grid") == "native_te"), "uncovered": int(r.get("grid") == "uncovered"),
                "correct": int(j["correct"]), "how": j["how"], "n_searches": len(s),
                "latin_q": sum(1 for x in s if x["script"] in LATIN), "mixed_q": sum(1 for x in s if x["script"] == "Mixed"),
                "any_gold": int(any(x["gold_hit"] for x in s)) if s else 0,
                "gold_calls": sum(1 for x in s if x["gold_hit"]),
                "cost": r.get("cost") or 0.0, "tin": r.get("tin") or 0, "tout": r.get("tout") or 0,
                "empty_ans": int(not (r.get("answer") or "").strip()),
            })
    return pd.DataFrame(rows)


def pool_to_E(pool, lang):
    if pool in (None, "none", "oracle"):
        return pool or "closed"
    if pool == "en":
        return "en"
    if pool == lang:
        return "L"
    if pool == f"{lang}+en":
        return "both"
    return pool


# ---------- statistics ----------
def boot_mean(x, n=N_BOOT):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(axis=1)
    return (float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def paired(a, b, n_perm=N_PERM):
    """a, b: dicts item -> value. Returns mean delta (a-b), bootstrap CI, sign-flip permutation p (two-sided)."""
    common = sorted(set(a) & set(b))
    if len(common) < 5:
        return {"n": len(common), "delta": np.nan, "ci": [np.nan, np.nan], "p": np.nan}
    d = np.array([a[i] - b[i] for i in common], dtype=float)
    m, lo, hi = boot_mean(d)
    signs = RNG.choice([-1, 1], size=(n_perm, len(d)))
    null = (signs * d).mean(axis=1)
    p = float((np.abs(null) >= abs(d.mean()) - 1e-12).mean())
    return {"n": len(common), "delta": m, "ci": [lo, hi], "p": p, "mean_a": float(np.mean([a[i] for i in common])),
            "mean_b": float(np.mean([b[i] for i in common]))}


def interaction(cells, n_perm=N_PERM_INTER):
    """2x2 interaction on paired items: (a1-a0) - (b1-b0) where cells = {('a',1): {item: v}, ...}.
    Permutation: shuffle the second-factor label within item."""
    items = sorted(set.intersection(*[set(v) for v in cells.values()]))
    if len(items) < 5:
        return {"n": len(items), "delta": np.nan, "p": np.nan}
    a1 = np.array([cells[("a", 1)][i] for i in items]); a0 = np.array([cells[("a", 0)][i] for i in items])
    b1 = np.array([cells[("b", 1)][i] for i in items]); b0 = np.array([cells[("b", 0)][i] for i in items])
    obs = (a1 - a0).mean() - (b1 - b0).mean()
    null = np.empty(n_perm)
    for k in range(n_perm):
        flip = RNG.random(len(items)) < 0.5
        A1 = np.where(flip, b1, a1); A0 = np.where(flip, b0, a0)
        B1 = np.where(flip, a1, b1); B0 = np.where(flip, a0, b0)
        null[k] = (A1 - A0).mean() - (B1 - B0).mean()
    d = (a1 - a0) - (b1 - b0)
    m, lo, hi = boot_mean(d)
    return {"n": len(items), "delta": float(obs), "ci": [lo, hi], "p": float((np.abs(null) >= abs(obs) - 1e-12).mean())}


def bh(pvals, q=0.05):
    keys = [k for k, p in pvals.items() if p is not None and not np.isnan(p)]
    ps = np.array([pvals[k] for k in keys])
    order = np.argsort(ps)
    m = len(ps)
    surv = set()
    thresh = 0.0
    for rank, idx in enumerate(order, 1):
        if ps[idx] <= q * rank / m:
            thresh = q * rank / m
    for k, p in zip(keys, ps):
        if p <= thresh:
            surv.add(k)
    return {"m": m, "q": q, "threshold": float(thresh), "survivors": sorted(surv)}


# ---------- main ----------
def cell_map(df, qlang, policy, E, retriever="dense"):
    sub = df[(df.qlang == qlang) & (df.policy == policy) & (df.E == E) & (df.rep == 0) & (df.retriever == retriever)]
    return dict(zip(sub.item, sub.correct))


def analyse_model(df, model):
    d_all = df[df.model == model]
    d = d_all[(d_all.native == 0) & (d_all.uncovered == 0)]
    out = {"n_records": int(len(d_all)), "spend_usd": float(d_all.cost.sum())}
    tests = {}
    unc = d_all[d_all.uncovered == 1]
    if len(unc):
        out["uncovered"] = {}
        for lang in sorted(unc.lang.unique()):
            u = unc[(unc.lang == lang) & (unc.rep == 0)]
            cells = {}
            for (q, p, E), g in u.groupby(["qlang", "policy", "E"]):
                m, lo, hi = boot_mean(g.correct.values)
                cells[f"{q}|{p}|{E}"] = {"n": int(len(g)), "acc": m, "ci": [lo, hi], "latin_share": float(g.latin_q.sum() / max(1, g.n_searches.sum())), "any_gold": float(g.any_gold.mean()), "abstain": float(g.abstain.mean())}
            cm = lambda q, p, E: dict(zip(u[(u.qlang == q) & (u.policy == p) & (u.E == E)].item, u[(u.qlang == q) & (u.policy == p) & (u.E == E)].correct))
            con = {"total_gap_free_both": paired(cm("en", "free", "both"), cm("L", "free", "both")),
                   "total_gap_free_en": paired(cm("en", "free", "en"), cm("L", "free", "en")),
                   "QG_recover_dual": paired(cm("L", "dual", "both"), cm("L", "free", "both")),
                   "EG_both_minus_ENonly": paired(cm("L", "free", "both"), cm("L", "free", "en")),
                   "closed_gap": paired(cm("en", "closed", "closed"), cm("L", "closed", "closed"))}
            # measured real-user accuracy: covered items (factorial, both pools) weighted by Cov, uncovered items (English-only pool) by 1-Cov
            cov = coverage(lang)["cov_verified"]
            covered = d[(d.lang == lang) & (d.source == "xorqa_in") & (d.rep == 0) & (d.retriever == "dense")]
            meas = {}
            for p_ in ("free", "dual"):
                a_cov = covered[(covered.qlang == "L") & (covered.policy == p_) & (covered.E == "both")].correct.mean()
                a_unc = u[(u.qlang == "L") & (u.policy == p_) & (u.E == "both" if p_ == "dual" else "en")].correct.mean() if p_ == "dual" else u[(u.qlang == "L") & (u.policy == "free") & (u.E == "en")].correct.mean()
                pooled_n = int(((covered.qlang == "L") & (covered.policy == p_) & (covered.E == "both")).sum() + ((u.qlang == "L") & (u.policy == p_)).sum())
                meas[p_] = {"acc_covered_both": float(a_cov), "acc_uncovered_en": float(a_unc), "measured_wild": float(cov * a_cov + (1 - cov) * a_unc),
                            "extrapolated_wild": float(cov * a_cov + (1 - cov) * covered[(covered.qlang == "L") & (covered.policy == p_) & (covered.E == "en")].correct.mean())}
            en_ref_cov = covered[(covered.qlang == "en") & (covered.policy == "free") & (covered.E == "en")].correct.mean()
            en_ref_unc = u[(u.qlang == "en") & (u.policy == "free") & (u.E == "en")].correct.mean()
            meas["english_user_measured"] = float(cov * en_ref_cov + (1 - cov) * en_ref_unc)
            # whole-population plain accuracy (all 539 XorQA items, Indic question, English-only pool = what the live Hindi Wikipedia lacks is unavailable anyway)
            out["uncovered"][lang] = {"cells": cells, "contrasts": con, "measured_decomposition": meas, "n_items": int(u.item.nunique())}
            for k, v in con.items():
                tests[f"{lang}:uncovered:{k}"] = v.get("p")
    nat = d_all[d_all.native == 1]
    if len(nat):
        out["native_te"] = {}
        for (q, p, E), g in nat[nat.rep == 0].groupby(["qlang", "policy", "E"]):
            m, lo, hi = boot_mean(g.correct.values)
            out["native_te"][f"{q}|{p}|{E}"] = {"n": int(len(g)), "acc": m, "ci": [lo, hi],
                                                "latin_share": float(g.latin_q.sum() / max(1, g.n_searches.sum())), "any_gold": float(g.any_gold.mean())}
        # same cells on the translated Telugu XorQA items for the translation-artefact comparison
        tr = d[(d.lang == "te") & (d.source == "xorqa_in") & (d.rep == 0) & (d.retriever == "dense")]
        out["native_te_vs_translated"] = {}
        for k in out["native_te"]:
            q, p, E = k.split("|")
            g = tr[(tr.qlang == q) & (tr.policy == p) & (tr.E == E)]
            if len(g):
                m, lo, hi = boot_mean(g.correct.values)
                out["native_te_vs_translated"][k] = {"translated_acc": m, "translated_ci": [lo, hi], "translated_n": int(len(g)),
                                                     "translated_latin_share": float(g.latin_q.sum() / max(1, g.n_searches.sum()))}
    for lang in sorted(d.lang.unique()):
        dl = d[(d.lang == lang)]
        L = {}
        # cell table
        cells = {}
        for (q, p, E, ret), g in dl[dl.rep == 0].groupby(["qlang", "policy", "E", "retriever"]):
            m, lo, hi = boot_mean(g.correct.values)
            cells[f"{q}|{p}|{E}" + ("" if ret == "dense" else f"|{ret}")] = {"n": int(len(g)), "acc": m, "ci": [lo, hi], "abstain": float(g.abstain.mean()),
                                     "latin_share": float(g.latin_q.sum() / max(1, g.n_searches.sum())),
                                     "mixed_share": float(g.mixed_q.sum() / max(1, g.n_searches.sum())),
                                     "any_gold": float(g.any_gold.mean()), "searches_per_episode": float(g.n_searches.mean()),
                                     "empty": float(g.empty_ans.mean()), "cost_per_episode": float(g.cost.mean()),
                                     "tin_per_episode": float(g.tin.mean())}
        L["cells"] = cells
        # core contrasts (BM25 grid)
        c = lambda q, p, E: cell_map(dl, q, p, E)
        con = {}
        con["total_gap_free_both"] = paired(c("en", "free", "both"), c("L", "free", "both"))
        con["QG_recover_dual"] = paired(c("L", "dual", "both"), c("L", "free", "both"))
        con["QG_recover_english"] = paired(c("L", "english", "both"), c("L", "free", "both"))
        con["QG_recover_match"] = paired(c("L", "match", "both"), c("L", "free", "both"))
        con["EG_both_minus_Lonly"] = paired(c("L", "free", "both"), c("L", "free", "L"))
        con["EG_both_minus_ENonly"] = paired(c("L", "free", "both"), c("L", "free", "en"))
        con["english_policy_on_ENonly"] = paired(c("L", "english", "en"), c("L", "match", "en"))
        con["english_policy_on_Lonly"] = paired(c("L", "english", "L"), c("L", "match", "L"))
        con["symmetric_monolingual"] = paired(c("en", "match", "en"), c("L", "match", "L"))
        con["en_user_dual_on_Lonly"] = paired(c("en", "dual", "L"), c("en", "free", "L"))
        con["IG_oracle_en"] = paired(cell_map(dl, "en", "oracle_en", "oracle"), cell_map(dl, "L", "oracle_en", "oracle"))
        con["closed_gap"] = paired(cell_map(dl, "en", "closed", "closed"), cell_map(dl, "L", "closed", "closed"))
        # retriever factor (D5): symmetric monolingual deficit under bm25 vs dense vs hybrid
        for ret in ("bm25", "hybrid"):
            con[f"symmetric_monolingual_{ret}"] = paired(cell_map(dl, "en", "match", "en", ret), cell_map(dl, "L", "match", "L", ret))
            con[f"total_gap_free_both_{ret}"] = paired(cell_map(dl, "en", "free", "both", ret), cell_map(dl, "L", "free", "both", ret))
            con[f"L_free_both_{ret}_minus_dense"] = paired(cell_map(dl, "L", "free", "both", ret), c("L", "free", "both"))
            con[f"QG_recover_dual_{ret}"] = paired(cell_map(dl, "L", "dual", "both", ret), cell_map(dl, "L", "free", "both", ret))
        L["contrasts"] = con
        L["interaction_policy_x_evidence"] = interaction({
            ("a", 1): c("L", "english", "en"), ("a", 0): c("L", "match", "en"),
            ("b", 1): c("L", "english", "L"), ("b", 0): c("L", "match", "L")})
        for k, v in con.items():
            tests[f"{lang}:{k}"] = v.get("p")
        tests[f"{lang}:interaction_policy_x_evidence"] = L["interaction_policy_x_evidence"].get("p")
        # mediator: query language under free
        free = dl[(dl.qlang == "L") & (dl.policy == "free") & (dl.rep == 0)]
        L["free_latin_share_by_E"] = {E: float(g.latin_q.sum() / max(1, g.n_searches.sum())) for E, g in free.groupby("E")}
        # attribution: correct answers with a gold hit
        agent = dl[(dl.rep == 0) & (dl.E.isin(["en", "L", "both"]))]
        L["attribution_rate"] = float(agent[agent.correct == 1].any_gold.mean()) if (agent.correct == 1).any() else np.nan
        L["gold_hit_rate_by_cell"] = {k: v["any_gold"] for k, v in cells.items()}
        # noise floor
        rep = dl[dl.rep > 0]
        if len(rep):
            base = cell_map(dl, "L", "free", "both")
            agree = []
            for it, g in rep.groupby("item"):
                vals = list(g.correct.values) + ([base[it]] if it in base else [])
                agree.append(1.0 if len(set(vals)) == 1 else 0.0)
            L["noise_floor"] = {"n_items": len(agree), "share_items_stable": float(np.mean(agree)),
                                "acc_sd_across_reps": float(rep.groupby("item").correct.std().mean())}
        # per-source breakdown of the headline cells (XorQA translated questions vs MLQA natively parallel)
        L["by_source"] = {}
        for src, g in dl[(dl.rep == 0) & (dl.retriever == "dense")].groupby("source"):
            cs = {}
            for (q, p, E), gg in g.groupby(["qlang", "policy", "E"]):
                if (q, p, E) in {("en", "free", "both"), ("L", "free", "both"), ("L", "dual", "both"), ("L", "english", "both"), ("L", "free", "en"), ("L", "free", "L"), ("en", "oracle_en", "oracle"), ("L", "oracle_en", "oracle"), ("en", "closed", "closed"), ("L", "closed", "closed")}:
                    cs[f"{q}|{p}|{E}"] = {"n": int(len(gg)), "acc": float(gg.correct.mean())}
            L["by_source"][src] = cs
        # search behaviour: how often the agent searched at all, and gold-hit rate per call
        beh = dl[(dl.rep == 0) & (dl.E.isin(["en", "L", "both"]))]
        L["search_behaviour"] = {f"{q}|{p}|{E}" + ("" if ret == "dense" else f"|{ret}"): {"searched_share": float((g.n_searches > 0).mean()), "gold_calls_per_search": float(g.gold_calls.sum() / max(1, g.n_searches.sum()))}
                                 for (q, p, E, ret), g in beh.groupby(["qlang", "policy", "E", "retriever"])}
        # secondary analysis (pre-specified 2026-10-10 19:15, before any grid result was read): the "needs-search"
        # subset = items the model answered wrongly closed-book in BOTH question languages; the same contrasts there.
        cb_en = cell_map(dl, "en", "closed", "closed"); cb_L = cell_map(dl, "L", "closed", "closed")
        ns = {i for i in cb_en if cb_en[i] == 0 and cb_L.get(i) == 0}
        L["needs_search_n"] = len(ns)
        if len(ns) >= 10:
            dns = dl[dl.item.isin(ns)]
            cn = lambda q, p, E: cell_map(dns, q, p, E)
            L["needs_search_contrasts"] = {
                "total_gap_free_both": paired(cn("en", "free", "both"), cn("L", "free", "both")),
                "QG_recover_dual": paired(cn("L", "dual", "both"), cn("L", "free", "both")),
                "QG_recover_english": paired(cn("L", "english", "both"), cn("L", "free", "both")),
                "EG_both_minus_Lonly": paired(cn("L", "free", "both"), cn("L", "free", "L")),
                "EG_both_minus_ENonly": paired(cn("L", "free", "both"), cn("L", "free", "en")),
            }
            L["needs_search_cells"] = {f"{q}|{p}|{E}": {"n": int(len(g)), "acc": float(g.correct.mean())}
                                       for (q, p, E), g in dns[(dns.rep == 0) & (dns.retriever == "dense")].groupby(["qlang", "policy", "E"])}
            for k, v in L["needs_search_contrasts"].items():
                tests[f"{lang}:needs_search:{k}"] = v.get("p")
        # decomposition in the wild
        cov = coverage(lang)
        L["coverage"] = cov
        dec = {}
        for p in ("free", "dual", "english", "match"):
            both = cells.get(f"L|{p}|both", {}).get("acc", np.nan)
            enonly = cells.get(f"L|{p}|en", {}).get("acc", np.nan)
            if not np.isnan(both) and not np.isnan(enonly):
                dec[p] = {"acc_wild": cov["cov_verified"] * both + (1 - cov["cov_verified"]) * enonly,
                          "term_covered": cov["cov_verified"] * both, "term_uncovered": (1 - cov["cov_verified"]) * enonly,
                          "acc_both": both, "acc_enonly": enonly}
        L["decomposition_wild"] = dec
        decb = {}
        for p in ("free", "dual", "english", "match"):
            both = cells.get(f"L|{p}|both|bm25", {}).get("acc", np.nan)
            enonly = cells.get(f"L|{p}|en|bm25", {}).get("acc", np.nan)
            if not np.isnan(both) and not np.isnan(enonly):
                decb[p] = {"acc_wild": cov["cov_verified"] * both + (1 - cov["cov_verified"]) * enonly,
                           "term_covered": cov["cov_verified"] * both, "term_uncovered": (1 - cov["cov_verified"]) * enonly,
                           "acc_both": both, "acc_enonly": enonly}
        L["decomposition_wild_bm25"] = decb
        out[lang] = L
    out["bh"] = bh(tests)
    out["tests"] = tests
    return out


def coverage(lang):
    xs = [it for it in ITEMS.values() if it["source"] == "xorqa_in" and it["lang"] == lang]
    n = len(xs)
    art = sum(1 for it in xs if it["cov_L_article"])
    strg = sum(1 for it in xs if it["cov_L_answer"])
    ver = sum(1 for it in xs if it.get("cov_L_verified"))
    m, lo, hi = boot_mean([1.0 if it.get("cov_L_verified") else 0.0 for it in xs])
    return {"n": n, "cov_article": art / n, "cov_string": strg / n, "cov_verified": ver / n, "cov_verified_ci": [lo, hi]}


def main():
    df = load()
    if df.empty:
        print("no judged records")
        return
    res = {"n_records": int(len(df)), "models": {}, "items_factorial": {
        lang: int(sum(1 for it in ITEMS.values() if it["lang"] == lang and it.get("factorial"))) for lang in ("hi", "te")}}
    for model in sorted(df.model.unique()):
        res["models"][model] = analyse_model(df, model)
    allt = {f"{m}:{k}": p for m, r in res["models"].items() for k, p in r["tests"].items()}
    res["bh_global"] = bh(allt)
    json.dump(res, open(OUT, "w"), indent=1, default=float)
    print("wrote", OUT, "records", len(df))
    for model, r in res["models"].items():
        print("\n==", model, f"${r['spend_usd']:.3f}")
        for lang in ("hi", "te"):
            if lang not in r:
                continue
            print(f"  [{lang}] cells:")
            for k, v in sorted(r[lang]["cells"].items()):
                print(f"     {k:28s} n={v['n']:3d} acc={v['acc']:.3f} [{v['ci'][0]:.2f},{v['ci'][1]:.2f}] latin={v['latin_share']:.2f} gold={v['any_gold']:.2f}")
            for k, v in r[lang]["contrasts"].items():
                if not np.isnan(v.get("delta", np.nan)):
                    print(f"     {k:28s} d={v['delta']:+.3f} [{v['ci'][0]:+.2f},{v['ci'][1]:+.2f}] p={v['p']:.4f} n={v['n']}")
            print("     interaction:", r[lang]["interaction_policy_x_evidence"])
        print("  BH:", r["bh"])


if __name__ == "__main__":
    main()
