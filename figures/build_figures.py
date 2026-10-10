#!/usr/bin/env python3
"""Build figures 2-5 from results/analysis.json only. Each figure prints the numbers it drew.
Fig 1 (teaser) is built separately from fig1_teaser.html through headless Chrome."""

import json
import pathlib
import sys

import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import style as S  # noqa: E402

S.apply()
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "Devanagari MT", "Telugu MN"]
ROOT = HERE.parent
A = json.load(open(ROOT / "results" / "analysis.json"))
OUT = ROOT / "paper" / "iclr" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
DOCS = ROOT / "docs" / "assets"
DOCS.mkdir(parents=True, exist_ok=True)

LABEL = {"google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite", "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite",
         "google/gemini-3.6-flash": "Gemini 3.6 Flash", "modal/Qwen3-30B-A3B-Instruct-2507": "Qwen3-30B-A3B"}
MODELS = [m for m in LABEL if m in A["models"]]
LANGS = [l for l in ("hi", "te")]
LANG_NAME = {"hi": "Hindi", "te": "Telugu"}
POL_COL = {"free": S.SLATE, "match": S.SHELF, "english": S.HOT, "dual": S.GOOD}
E_LABEL = {"en": "English-only pool", "L": "Indic-only pool", "both": "both"}


def cell(m, lang, q, p, e, ret=None):
    key = f"{q}|{p}|{e}" + (f"|{ret}" if ret else "")
    return A["models"][m].get(lang, {}).get("cells", {}).get(key)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(DOCS / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("wrote", name)


def fig2_query_language():
    """Share of Latin-script (English) search queries under the free policy, by question language and pool."""
    fig, axes = plt.subplots(1, len(MODELS), figsize=(3.4 * len(MODELS) + 1, 3.6), sharey=True, squeeze=False)
    for ax, m in zip(axes[0], MODELS):
        xs, vals, cols, labs = [], [], [], []
        k = 0
        for lang in LANGS:
            for e in ("en", "both", "L"):
                c = cell(m, lang, "L", "free", e)
                if not c:
                    continue
                xs.append(k); vals.append(c["latin_share"]); cols.append(S.HOT if lang == "hi" else S.SHELF)
                labs.append(f"{LANG_NAME[lang][:2]}\n{ {'en': 'EN', 'both': 'both', 'L': 'IND'}[e] }")
                ax.text(k, c["latin_share"] + 0.02, f"{100 * c['latin_share']:.0f}%", ha="center", fontsize=8, color=S.INK2)
                k += 1
            k += 0.6
        ax.bar(xs, vals, color=cols, width=0.8, zorder=2)
        ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=7.5)
        ax.set_ylim(0, 1.08); ax.axhline(0.5, color=S.FAINT, lw=0.8, ls="--")
        ax.set_title(LABEL[m], fontsize=10, color=S.INK, loc="left", pad=4)
        S.clean(ax)
        print("fig2", m, [(l, round(v, 2)) for l, v in zip(labs, vals)])
    axes[0][0].set_ylabel("share of search queries written in English")
    S.eyebrow(axes[0][0], "Free policy, Indic question: in what language does the agent search?", y=1.13)
    save(fig, "fig2_query_language")


def fig3_policy_by_pool():
    """Accuracy of the Indic question by policy and served pool; English-question reference as a dashed line."""
    fig, axes = plt.subplots(len(LANGS), len(MODELS), figsize=(3.6 * len(MODELS) + 1, 3.0 * len(LANGS) + 0.6), squeeze=False, sharey=True)
    for i, lang in enumerate(LANGS):
        for j, m in enumerate(MODELS):
            ax = axes[i][j]
            w = 0.19
            for ei, e in enumerate(("en", "L", "both")):
                for pi, p in enumerate(("free", "match", "english", "dual")):
                    c = cell(m, lang, "L", p, e)
                    if not c:
                        continue
                    x = ei + (pi - 1.5) * w
                    ax.bar(x, c["acc"], w, color=POL_COL[p], zorder=2, label=p if (ei == 0 and i == 0 and j == 0) else None)
                    ax.plot([x, x], c["ci"], color=S.INK2, lw=0.7, zorder=3)
                ref = cell(m, lang, "en", "free", e)
                if ref:
                    ax.plot([ei - 0.42, ei + 0.42], [ref["acc"]] * 2, color=S.INK, lw=1.0, ls="--", zorder=4)
            ax.set_xticks([0, 1, 2]); ax.set_xticklabels([E_LABEL[e] for e in ("en", "L", "both")], fontsize=8)
            ax.set_ylim(0, 1.0)
            if j == 0:
                ax.set_ylabel(f"{LANG_NAME[lang]} question: accuracy")
            if i == 0:
                ax.set_title(LABEL[m], fontsize=10, color=S.INK, loc="left", pad=4)
            S.clean(ax)
    axes[0][0].legend(frameon=False, fontsize=8, loc="upper left", ncol=4, title="query policy", title_fontsize=8)
    S.eyebrow(axes[0][0], "Dashed: same question asked in English (free policy). Bars: Indic question under four query policies, by served pool.", y=1.13)
    save(fig, "fig3_policy_by_pool")


def fig4_decomposition():
    """Real-world decomposition: coverage-weighted accuracy for the Indic user under free and dual, vs the English user."""
    fig, axes = plt.subplots(1, len(MODELS), figsize=(3.4 * len(MODELS) + 2.5, 3.8), sharey=True, squeeze=False, gridspec_kw={"width_ratios": [2.2 if m == MODELS[0] else 1 for m in MODELS]})
    for ax, m in zip(axes[0], MODELS):
        k = 0
        xs, labs = [], []
        for lang in LANGS:
            R = A["models"][m].get(lang, {})
            dec = R.get("decomposition_wild", {})
            cov = R.get("coverage", {}).get("cov_verified", np.nan)
            for p in ("free", "dual"):
                if p not in dec:
                    continue
                d = dec[p]
                ax.bar(k, d["term_covered"], color=S.SLATE, width=0.7, zorder=2)
                ax.bar(k, d["term_uncovered"], bottom=d["term_covered"], color=S.SHELF, width=0.7, zorder=2)
                ax.text(k, d["acc_wild"] + 0.02, f"{100 * d['acc_wild']:.0f}", ha="center", fontsize=8, color=S.INK2)
                xs.append(k); labs.append(f"{LANG_NAME[lang][:2]}\n{p}")
                print("fig4", m, lang, p, {kk: round(v, 3) for kk, v in d.items()}, "cov", round(cov, 3))
                k += 1
            ref = cell(m, lang, "en", "free", "en")
            if ref:
                ax.bar(k, ref["acc"], color=S.INK, width=0.7, zorder=2, alpha=0.85)
                ax.text(k, ref["acc"] + 0.02, f"{100 * ref['acc']:.0f}", ha="center", fontsize=8, color=S.INK2)
                xs.append(k); labs.append(f"{LANG_NAME[lang][:2]}\nEN user")
                k += 1
            decb = R.get("decomposition_wild_bm25", {})
            for p in ("free", "english"):
                if p in decb:
                    d = decb[p]
                    ax.bar(k, d["term_covered"], color=S.SLATE, width=0.7, zorder=2, hatch="///", edgecolor="white")
                    ax.bar(k, d["term_uncovered"], bottom=d["term_covered"], color=S.SHELF, width=0.7, zorder=2, hatch="///", edgecolor="white")
                    ax.text(k, d["acc_wild"] + 0.02, f"{100 * d['acc_wild']:.0f}", ha="center", fontsize=8, color=S.INK2)
                    xs.append(k); labs.append(f"{LANG_NAME[lang][:2]}\n{p}\nBM25")
                    print("fig4 bm25", m, lang, p, round(d["acc_wild"], 3))
                    k += 1
            refb = cell(m, lang, "en", "free", "en", "bm25")
            if refb:
                ax.bar(k, refb["acc"], color=S.INK, width=0.7, zorder=2, alpha=0.85, hatch="///", edgecolor="white")
                ax.text(k, refb["acc"] + 0.02, f"{100 * refb['acc']:.0f}", ha="center", fontsize=8, color=S.INK2)
                xs.append(k); labs.append(f"{LANG_NAME[lang][:2]}\nEN user\nBM25")
                k += 1
            k += 0.6
        ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=7.5)
        ax.set_ylim(0, 1.05)
        ax.set_title(LABEL[m], fontsize=10, color=S.INK, loc="left", pad=4)
        S.clean(ax)
    axes[0][0].set_ylabel("expected accuracy for a real user")
    S.eyebrow(axes[0][0], "Indic user's accuracy = Cov x Acc(evidence in L) [slate] + (1 - Cov) x Acc(evidence only in English) [shelf]; black: English user; hatched: BM25", y=1.13)
    save(fig, "fig4_decomposition")


def fig5_retriever_oracle():
    """Retriever factor and ceilings: Q=L free/both under dense vs BM25, closed-book, oracle, per language and model."""
    fig, axes = plt.subplots(1, len(LANGS), figsize=(4.6 * len(LANGS), 3.6), sharey=True, squeeze=False)
    for ax, lang in zip(axes[0], LANGS):
        w = 0.15
        series = [("closed-book", lambda m: cell(m, lang, "L", "closed", "closed"), S.FAINT),
                  ("BM25 search", lambda m: cell(m, lang, "L", "free", "both", "bm25"), S.SHELF),
                  ("dense search", lambda m: cell(m, lang, "L", "free", "both"), S.SLATE),
                  ("oracle passage", lambda m: cell(m, lang, "L", "oracle_en", "oracle"), S.GOOD),
                  ("English question, dense", lambda m: cell(m, lang, "en", "free", "both"), S.INK)]
        for si, (name, f, col) in enumerate(series):
            for mi, m in enumerate(MODELS):
                c = f(m)
                if not c:
                    continue
                x = mi + (si - 2) * w
                ax.bar(x, c["acc"], w, color=col, zorder=2, label=name if mi == 0 else None)
                ax.plot([x, x], c["ci"], color=S.INK2, lw=0.7, zorder=3)
                print("fig5", lang, m, name, round(c["acc"], 3))
        ax.set_xticks(range(len(MODELS))); ax.set_xticklabels([LABEL[m].replace(" ", "\n", 1) for m in MODELS], fontsize=8)
        ax.set_ylim(0, 1.0); ax.set_title(f"{LANG_NAME[lang]} question", fontsize=10, color=S.INK, loc="left")
        S.clean(ax)
    axes[0][0].set_ylabel("accuracy")
    axes[0][0].legend(frameon=False, fontsize=8, loc="upper left", ncol=3)
    S.eyebrow(axes[0][0], "What the retriever adds, what the passage adds, and the English-question reference", y=1.13)
    save(fig, "fig5_retriever_oracle")


if __name__ == "__main__":
    for f in (fig2_query_language, fig3_policy_by_pool, fig4_decomposition, fig5_retriever_oracle):
        try:
            f()
        except Exception as ex:
            print("SKIP", f.__name__, type(ex).__name__, ex)
