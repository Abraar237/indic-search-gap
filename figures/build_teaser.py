#!/usr/bin/env python3
"""Fig 1 teaser: an HTML page filled from results/analysis.json, rendered with headless Chrome to
paper/iclr/assets/fig1_teaser.png and docs/assets/fig1_teaser.png. Standard fonts, white background,
house palette. Three panels: (a) the design, (b) in what language the agent searches, (c) the decomposition."""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
A = json.load(open(ROOT / "results" / "analysis.json"))
MODEL = sys.argv[1] if len(sys.argv) > 1 else "google/gemini-2.5-flash-lite"
M = A["models"][MODEL]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def pct(x):
    return f"{100 * x:.0f}"


def cell(lang, key):
    return M.get(lang, {}).get("cells", {}).get(key, {})


rows_b = []
for lang, name in (("hi", "Hindi"), ("te", "Telugu")):
    for e, el in (("en", "English-only pool"), ("L", f"{name}-only pool"), ("both", "both")):
        c = cell(lang, f"L|free|{e}")
        if c:
            rows_b.append((f"{name} question, {el}", c["latin_share"]))
rows_c = []
for lang, name in (("hi", "Hindi"), ("te", "Telugu")):
    R = M.get(lang, {})
    dec = R.get("decomposition_wild", {})
    cov = R.get("coverage", {}).get("cov_verified", float("nan"))
    ref = cell(lang, "en|free|en").get("acc", float("nan"))
    mu = M.get("uncovered", {}).get(lang, {}).get("measured_decomposition")
    for p in ("free", "dual"):
        if mu and p in mu:
            d = mu[p]
            rows_c.append((name, p + " (measured)", cov * d["acc_covered_both"], (1 - cov) * d["acc_uncovered_en"], d["measured_wild"], mu["english_user_measured"], cov))
        elif p in dec:
            d = dec[p]
            rows_c.append((name, p, d["term_covered"], d["term_uncovered"], d["acc_wild"], ref, cov))


def bars_b():
    out = []
    for lab, v in rows_b:
        out.append(f'<div class="row"><div class="lab">{lab}</div><div class="track"><div class="fill hot" style="width:{100 * v:.1f}%"></div></div><div class="num">{pct(v)}%</div></div>')
    return "\n".join(out)


def bars_c():
    out = []
    for name, p, cov_t, unc_t, wild, ref, cov in rows_c:
        out.append(f'<div class="row"><div class="lab">{name} user, <span class="mono">{p}</span></div><div class="track">'
                   f'<div class="fill slate" style="width:{100 * cov_t:.1f}%"></div><div class="fill shelf" style="width:{100 * unc_t:.1f}%"></div>'
                   f'<div class="tick" style="left:{100 * ref:.1f}%"></div></div><div class="num">{pct(wild)}</div></div>')
    return "\n".join(out)


html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#fff;font-family:Helvetica,Arial,sans-serif;color:#16130d;width:2400px}}
.wrap{{display:grid;grid-template-columns:1.05fr 1fr 1fr;gap:48px;padding:48px 56px}}
.eyebrow{{font-size:22px;letter-spacing:.12em;text-transform:uppercase;color:#6d665a;font-weight:700;margin-bottom:10px}}
h2{{font-size:38px;margin:0 0 22px;line-height:1.2}}
.design{{font-size:27px;line-height:1.5}}
.design b{{color:#155e8c}}
.box{{border:2px solid #e7e2d5;border-radius:12px;padding:18px 22px;margin:12px 0;font-size:26px}}
.row{{display:grid;grid-template-columns:330px 1fr 90px;align-items:center;gap:16px;margin:14px 0;font-size:25px}}
.track{{position:relative;height:36px;background:#f3f0e8;border-radius:6px;overflow:visible;display:flex}}
.fill{{height:100%}} .hot{{background:#b3006b}} .slate{{background:#155e8c}} .shelf{{background:#c0641a}}
.tick{{position:absolute;top:-8px;width:4px;height:52px;background:#16130d}}
.num{{font-family:Menlo,monospace;font-size:26px;text-align:right}}
.mono{{font-family:Menlo,monospace;font-size:23px}}
.legend{{font-size:22px;color:#6d665a;margin-top:14px;line-height:1.5}}
.sw{{display:inline-block;width:22px;height:22px;vertical-align:middle;border-radius:4px;margin-right:6px}}
</style></head><body><div class="wrap">
<div><div class="eyebrow">a · the instrument</div><h2>Same question, two languages; same web, served three ways</h2>
<div class="design">Parallel <b>Hindi/English</b> and <b>Telugu/English</b> questions whose answer is verifiably in both Wikipedias.
A search agent (3 searches, then answer) over a frozen pool served <b>English-only</b>, <b>Indic-only</b>, or <b>both</b>.
The script of every query is logged under a <b>free</b> policy, then the policy is forced: <b>match</b>, <b>english</b>, <b>dual</b>.</div>
<div class="box">query-side gap = what the agent's queries lose · evidence-side gap = what the web lacks · integration gap = what reading loses</div></div>
<div><div class="eyebrow">b · whose language does the agent search in?</div><h2>Share of queries written in English, free policy</h2>{bars_b()}
<div class="legend">Indic question; the agent chose the query language itself. {A['models'][MODEL].get('hi', {}).get('coverage', {}).get('n', '')} items per language.</div></div>
<div><div class="eyebrow">c · the real-world gap, decomposed</div><h2>Expected accuracy for a real Indic user</h2>{bars_c()}
<div class="legend"><span class="sw" style="background:#155e8c"></span>facts the Indic Wikipedia has (Cov × Acc) &nbsp; <span class="sw" style="background:#c0641a"></span>facts only English has ((1−Cov) × Acc, measured on those items) &nbsp; <span class="sw" style="background:#16130d"></span>English user's accuracy on the same mix.
Coverage measured on 539 questions per language: Hindi {pct(M.get('hi', {}).get('coverage', {}).get('cov_verified', 0))}%, Telugu {pct(M.get('te', {}).get('coverage', {}).get('cov_verified', 0))}%.</div></div>
</div></body></html>"""
(HERE / "fig1_teaser.html").write_text(html)
for out in (ROOT / "paper" / "iclr" / "assets" / "fig1_teaser.png", ROOT / "docs" / "assets" / "fig1_teaser.png"):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=2400,980",
                    f"--screenshot={out}", str(HERE / "fig1_teaser.html")], check=True, capture_output=True)
    print("wrote", out)
