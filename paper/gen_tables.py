#!/usr/bin/env python3
"""Generate LaTeX tables from results/analysis.json: paper/iclr/tables_main.tex (headline contrasts with BH
marks), tables_cells.tex (every cell per model and language), tables_decomp.tex (decomposition), tables_cost.tex.
Bold = survives the global Benjamini-Hochberg family."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = json.load(open(ROOT / "results" / "analysis.json"))
OUT = ROOT / "paper" / "iclr"
SURV = set(A["bh_global"]["survivors"])
LABEL = {"google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite", "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite",
         "google/gemini-3.6-flash": "Gemini 3.6 Flash", "modal/Qwen3-30B-A3B-Instruct-2507": "Qwen3-30B-A3B"}
MODELS = [m for m in LABEL if m in A["models"]]
LN = {"hi": "Hindi", "te": "Telugu"}
CON = [("total_gap_free_both", "Total gap: English minus Indic question (free, both pools)"),
       ("QG_recover_dual", "Recovered by dual-language queries"),
       ("QG_recover_english", "Recovered by English-only queries"),
       ("QG_recover_match", "Recovered by matched-language queries"),
       ("EG_both_minus_ENonly", "Evidence-side: both pools minus English-only pool"),
       ("EG_both_minus_Lonly", "Evidence-side: both pools minus Indic-only pool"),
       ("english_policy_on_ENonly", "English queries minus matched queries, English-only pool"),
       ("english_policy_on_Lonly", "English queries minus matched queries, Indic-only pool"),
       ("symmetric_monolingual", "Symmetric monolingual: en/en minus L/L"),
       ("IG_oracle_en", "Integration gap: oracle passage, English minus Indic question"),
       ("closed_gap", "Closed-book gap"),
       ("total_gap_free_both_bm25", "Total gap under BM25"),
       ("symmetric_monolingual_bm25", "Symmetric monolingual under BM25"),
       ("QG_recover_dual_bm25", "Recovered by dual queries under BM25"),
       ("L_free_both_bm25_minus_dense", "Indic question: BM25 minus dense (free, both)")]


def fmt(v, key):
    if v is None or v.get("delta") is None or v.get("n", 0) < 10 or v["delta"] != v["delta"]:
        return "--"
    s = f"{100 * v['delta']:+.1f} [{100 * v['ci'][0]:+.1f}, {100 * v['ci'][1]:+.1f}]"
    if v['p'] < 0.05:
        s += "$^{*}$"
    return f"\\textbf{{{s}}}" if key in SURV else s


def main_table():
    lines = ["\\begin{table}[t]\\centering\\scriptsize", "\\resizebox{\\textwidth}{!}{", "\\begin{tabular}{p{5.6cm}" + "l" * (2 * len(MODELS)) + "}", "\\toprule",
             "Contrast (percentage points) & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{LABEL[m]}}}" for m in MODELS) + " \\\\",
             " & " + " & ".join("Hindi & Telugu" for _ in MODELS) + " \\\\", "\\midrule"]
    for k, desc in CON:
        row = [desc]
        for m in MODELS:
            for lang in ("hi", "te"):
                v = A["models"][m].get(lang, {}).get("contrasts", {}).get(k)
                row.append(fmt(v, f"{m}:{lang}:{k}"))
        lines.append(" & ".join(row) + " \\\\")
    lines.append("\\midrule")
    row = ["Policy $\\times$ evidence interaction"]
    for m in MODELS:
        for lang in ("hi", "te"):
            v = A["models"][m].get(lang, {}).get("interaction_policy_x_evidence")
            row.append(fmt(v, f"{m}:{lang}:interaction_policy_x_evidence") if v and v.get("n", 0) >= 10 else "--")
    lines.append(" & ".join(row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}}",
              f"\\caption{{Paired within-item contrasts (percentage points) with item-bootstrap 95\\% intervals. $^{{*}}$: sign-flip permutation $p<0.05$. Bold: survives Benjamini--Hochberg over the full family of {A['bh_global']['m']} tests (threshold $p \\le {A['bh_global']['threshold']:.4f}$). Positive total gap = the English question is answered more often. Dense retriever unless marked BM25.}}",
              "\\label{tab:main}", "\\end{table}"]
    (OUT / "tables_main.tex").write_text("\n".join(lines))


def cells_table():
    out = []
    for m in MODELS:
        for lang in ("hi", "te"):
            L = A["models"][m].get(lang)
            if not L:
                continue
            cells = L["cells"]
            out += ["\\begin{table}[h]\\centering\\scriptsize", "\\begin{tabular}{lllrrrrr}", "\\toprule",
                    "Question & Policy & Pool & n & Acc & 95\\% CI & English queries & gold in top-5 \\\\", "\\midrule"]
            for k in sorted(cells):
                q, p, E = (k.split("|") + [""])[:3]
                ret = k.split("|")[3] if k.count("|") == 3 else "dense"
                c = cells[k]
                pool = {"en": "English-only", "L": "Indic-only", "both": "both", "closed": "(no tool)", "oracle": "(gold passage)", "none": "(gold hidden)"}.get(E, E)
                if ret != "dense":
                    pool += f" [{ret}]"
                out.append(f"{'English' if q == 'en' else LN[lang]} & {p.replace('_', ' ')} & {pool} & {c['n']} & {100 * c['acc']:.1f} & [{100 * c['ci'][0]:.1f}, {100 * c['ci'][1]:.1f}] & {100 * c['latin_share']:.0f}\\% & {100 * c['any_gold']:.0f}\\% \\\\")
            out += ["\\bottomrule", "\\end{tabular}", f"\\caption{{All cells, {LABEL[m]}, {LN[lang]} items (n = items; `English queries' = share of search calls written in Latin script; `gold in top-5' = share of episodes in which a gold chunk was retrieved).}}", "\\end{table}", ""]
    (OUT / "tables_cells.tex").write_text("\n".join(out))


def decomp_table():
    lines = ["\\begin{table}[t]\\centering\\small", "\\resizebox{\\textwidth}{!}{", "\\begin{tabular}{llrrrrr}", "\\toprule",
             "Model & Language & Cov$_L$ & Indic user, free & Indic user, dual & Indic user, english & English user \\\\", "\\midrule"]
    for m in MODELS:
        for lang in ("hi", "te"):
            L = A["models"][m].get(lang)
            if not L or not L.get("decomposition_wild"):
                continue
            d = L["decomposition_wild"]; cov = L["coverage"]["cov_verified"]
            ref = L["cells"].get("en|free|en", {}).get("acc", float("nan"))
            g = lambda p: f"{100 * d[p]['acc_wild']:.1f}" if p in d else "--"
            lines.append(f"{LABEL[m]} & {LN[lang]} & {100 * cov:.1f}\\% & {g('free')} & {g('dual')} & {g('english')} & {100 * ref:.1f} \\\\")
            mu = A["models"][m].get("uncovered", {}).get(lang, {}).get("measured_decomposition")
            if mu:
                lines.append(f"\\quad measured on the uncovered items & {LN[lang]} & {100 * cov:.1f}\\% & {100 * mu['free']['measured_wild']:.1f} & {100 * mu['dual']['measured_wild']:.1f} & -- & {100 * mu['english_user_measured']:.1f} \\\\")
            db = L.get("decomposition_wild_bm25", {})
            if db:
                refb = L["cells"].get("en|free|en|bm25", {}).get("acc", float("nan"))
                gb = lambda p: f"{100 * db[p]['acc_wild']:.1f}" if p in db else "--"
                lines.append(f"\\quad under BM25 & {LN[lang]} & {100 * cov:.1f}\\% & {gb('free')} & {gb('dual')} & {gb('english')} & {100 * refb:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}}",
              "\\caption{Expected accuracy for a real user, Eq.~\\ref{eq:decomp}: Cov$_L$ is the share of the 539 XorQA questions whose Hindi or Telugu Wikipedia article verifiably states the answer; the Indic user's accuracy weights the both-pools cell by Cov$_L$ and the English-only cell by $1-$Cov$_L$; the English user is the English question on the English-only pool. `Measured' rows replace the extrapolated uncovered term by the direct run on the uncovered items (Section~\\ref{sec:results-decomp}).}",
              "\\label{tab:decomp}", "\\end{table}"]
    (OUT / "tables_decomp.tex").write_text("\n".join(lines))


def cost_table():
    sp = json.load(open(ROOT / "results" / "spend.json"))
    lines = ["\\begin{table}[h]\\centering\\small", "\\begin{tabular}{lr}", "\\toprule", "Stage & USD \\\\", "\\midrule"]
    for k, v in sorted(sp["by_stage"].items(), key=lambda x: -x[1]):
        lines.append(f"{k.replace(chr(95), chr(92)+chr(95))} & {v:.2f} \\\\")
    lines += ["\\midrule", f"Total metered through OpenRouter ({sp['n_calls']} calls) & {sp['total_usd']:.2f} \\\\", "\\bottomrule", "\\end{tabular}",
              "\\caption{Metered API spend (exact per-call \\texttt{usage.cost}). The open-weight arm ran on a rented A100 (about 2.5 GPU-hours) and the bge-m3 embeddings took about 0.5 GPU-hour; both outside the metered total.}", "\\label{tab:cost}", "\\end{table}"]
    (OUT / "tables_cost.tex").write_text("\n".join(lines))


if __name__ == "__main__":
    main_table(); cells_table(); decomp_table(); cost_table()
    print("tables written")
