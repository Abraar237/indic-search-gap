#!/usr/bin/env python3
"""Research film: 1920x1080 @ 60 fps, phrase-anchored to words.json (from tts.py). Visual system shared with the
site and paper figures: cream card, flat bars, Menlo bold titles, Helvetica labels, monospace numerals, continuous
motion, marker annotations landing on the spoken number. Numbers from results/analysis.json (Gemini 2.5 Flash-Lite).
  python3 build_film.py check   -> anchor check + one frame per scene (video/_check_*.png)
  python3 build_film.py         -> frames to video/frames/, then encode with encode.sh"""
import json, math, pathlib, shutil, sys
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FRAMES = HERE / "frames"
W, H, FPS = 1920, 1080, 60
INK = (22, 19, 13); INK2 = (58, 53, 43); MUTED = (109, 102, 90); FAINT = (164, 156, 140); RULE = (231, 226, 213); BG = (253, 252, 250)
SLATE = (21, 94, 140); HOT = (179, 0, 107); SHELF = (192, 100, 26); GOOD = (28, 122, 85); PURPLE = (122, 111, 155)
MENLO = "/System/Library/Fonts/Menlo.ttc"; HELV = "/System/Library/Fonts/Helvetica.ttc"
F = lambda p, s, i=0: ImageFont.truetype(p, s, index=i)
f_h1 = F(MENLO, 72, 1); f_h2 = F(MENLO, 52, 1); f_sub = F(HELV, 30); f_lab = F(HELV, 32); f_note = F(HELV, 26); f_eyebrow = F(HELV, 22)
f_num = F(MENLO, 40); f_big = F(MENLO, 120, 1); f_mono = F(MENLO, 34); f_mid = F(MENLO, 64, 1); f_body = F(HELV, 36)
A = json.load(open(ROOT / "results" / "analysis.json"))
FL = A["models"]["google/gemini-2.5-flash-lite"]
DB = json.load(open(HERE / "words.json")); CUE = {c["id"]: c for c in DB["cues"]}; TOTAL = DB["total"]
XFADE = 0.4


def norm(w):
    return w.lower().strip(".,;:!?\"'()-")


def toks(text):
    """split on spaces and hyphens (whisper emits 'forty -four' as two tokens)"""
    return [norm(p) for w in text.split() for p in w.split("-") if norm(p)]


def at(cue, phrase):
    c = CUE[cue]
    words, starts = [], []
    for w in c["words"]:
        for p in w["w"].split("-"):
            if norm(p):
                words.append(norm(p)); starts.append(w["s"])
    target = toks(phrase)
    for i in range(len(words) - len(target) + 1):
        if words[i:i + len(target)] == target:
            return c["start"] + starts[i]
    raise KeyError(f"phrase not found in {cue}: {phrase!r}")


def cue_start(cue):
    return CUE[cue]["start"]


def ease(x):
    return 0 if x <= 0 else 1 if x >= 1 else 0.5 - 0.5 * math.cos(math.pi * x)


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)


def mix(c1, c2, f):
    return tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


def cell(lang, k, f="acc"):
    return FL[lang]["cells"][k][f]


def base(d, t):
    d.rectangle([0, 0, W, H], fill=BG); d.rectangle([28, 28, W - 28, H - 28], outline=RULE, width=3)
    d.text((70, 62), "S E A R C H   I N   W H O S E   L A N G U A G E ?", font=f_eyebrow, fill=FAINT)
    d.text((W - 70, 62), "R E S E A R C H   F I L M", font=f_eyebrow, fill=FAINT, anchor="ra")
    for k in range(7):
        x = 70 + ((t * 42 + k * 260) % (W - 140)); d.ellipse([x - 4, H - 60, x + 4, H - 52], fill=mix(RULE, FAINT, 0.5))


def hbar(d, x, y, w, h, frac, color):
    d.rectangle([x, y, x + w, y + h], outline=RULE, width=3)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 6:
        d.rectangle([x + 3, y + 3, x + fw - 3, y + h - 3], fill=color)


def underline(d, x0, x1, y, g, color=HOT):
    if g > 0:
        d.line([(x0, y), (x0 + (x1 - x0) * g, y + 3)], fill=mix(BG, color, 0.55), width=9)


def ring(d, cx, cy, r, g, color=HOT):
    if g > 0:
        d.arc([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], start=-90, end=-90 + 360 * g, fill=mix(BG, color, 0.6), width=7)


def bars(d, t, rows, y0=330, x0=160, w=1100, step=140, scale=1.0, fmt="{:.0f}"):
    """rows: (label, value in [0,1], color, appear_time)"""
    for i, (lab, val, col, ta) in enumerate(rows):
        y = y0 + i * step; g = seg(t, ta, ta + 1.1)
        d.rectangle([x0, y + 30, x0 + w, y + 84], outline=RULE, width=3)  # track from scene start: no blank opening
        if g <= 0:
            continue
        d.text((x0, y), lab, font=f_lab, fill=mix(BG, INK, min(1, g * 3)), anchor="lm")
        hbar(d, x0, y + 30, w, 54, val * g / scale, col)
        if g > 0.99:
            d.text((x0 + w + 40, y + 57), fmt.format(100 * val), font=f_mid, fill=col, anchor="lm")


def wrap_text(d, text, font, x, y, maxw, fill, line_h):
    words = text.split(); line = ""; yy = y
    for w in words:
        test = (line + " " + w).strip()
        if d.textlength(test, font=font) > maxw and line:
            d.text((x, yy), line, font=font, fill=fill, anchor="lm"); yy += line_h; line = w
        else:
            line = test
    if line:
        d.text((x, yy), line, font=font, fill=fill, anchor="lm")


# ---------------------------------------------------------------- scenes
def s1(d, t):  # cold open: the setting
    d.text((W // 2, 230), "Search in whose language?", font=f_h1, fill=INK, anchor="mm")
    g = seg(t, at("p1", "They ask"), at("p1", "They ask") + 0.8)
    steps = [("ask", at("p1", "They ask")), ("search", at("p1", "the assistant searches")), ("read", at("p1", "reads what")), ("answer", at("p1", "and answers"))]
    for i, (lab, ta) in enumerate(steps):
        gg = seg(t, ta, ta + 0.6)
        if gg > 0:
            x = 420 + i * 300
            d.rounded_rectangle([x, 380, x + 220, 480], radius=18, outline=mix(BG, SLATE, gg), width=4, fill=mix(BG, SLATE, 0.06 * gg))
            d.text((x + 110, 430), lab, font=f_lab, fill=mix(BG, SLATE, gg), anchor="mm")
            if i:
                d.line([(x - 80, 430), (x - 10, 430)], fill=mix(BG, FAINT, gg), width=4)
    g2 = seg(t, at("p1", "When the question"), at("p1", "When the question") + 0.8)
    if g2 > 0:
        d.text((W // 2, 620), "a Hindi or Telugu question is answered wrong more often than the same question in English", font=f_body, fill=mix(BG, INK, g2), anchor="mm")
    g3 = seg(t, at("p1", "The question is why"), at("p1", "The question is why") + 0.8)
    if g3 > 0:
        d.text((W // 2, 780), "why?  the fix depends on the cause", font=f_mid, fill=mix(BG, HOT, g3), anchor="mm")


def s2(d, t):  # two causes
    d.text((W // 2, 170), "Two causes, two fixes", font=f_h2, fill=INK, anchor="mm")
    g1 = seg(t, at("p2", "The first is the agent"), at("p2", "The first is the agent") + 0.8)
    if g1 > 0:
        d.rounded_rectangle([140, 300, 940, 620], radius=18, outline=mix(BG, HOT, g1), width=4)
        d.text((540, 350), "the query-side gap", font=f_num, fill=mix(BG, HOT, g1), anchor="mm")
        wrap_text(d, "the agent writes a worse query, or searches in a language where the evidence is not", f_note, 180, 420, 720, mix(BG, INK2, g1), 38)
        d.text((540, 570), "fix: prompting, training", font=f_note, fill=mix(BG, MUTED, g1), anchor="mm")
    g2 = seg(t, at("p2", "The second is the web"), at("p2", "The second is the web") + 0.8)
    if g2 > 0:
        d.rounded_rectangle([980, 300, 1780, 620], radius=18, outline=mix(BG, SHELF, g2), width=4)
        d.text((1380, 350), "the evidence-side gap", font=f_num, fill=mix(BG, SHELF, g2), anchor="mm")
        wrap_text(d, "the fact was never written in the user's language; no query in that language can find it", f_note, 1020, 420, 720, mix(BG, INK2, g2), 38)
        d.text((1380, 570), "fix: cross-lingual search, new content", font=f_note, fill=mix(BG, MUTED, g2), anchor="mm")
    g3 = seg(t, at("p2", "Hindi Wikipedia has"), at("p2", "Hindi Wikipedia has") + 1.0)
    if g3 > 0:
        d.text((W // 2, 720), "Hindi Wikipedia: 2.4% of the articles of English Wikipedia", font=f_body, fill=mix(BG, INK, g3), anchor="mm")
        hbar(d, 460, 780, 1000, 40, 1.0 * g3, mix(BG, INK, 0.85)); hbar(d, 460, 840, 1000, 40, 0.024 * g3, SHELF)
        d.text((1480, 800), "English", font=f_note, fill=mix(BG, MUTED, g3), anchor="lm"); d.text((1480, 860), "Hindi", font=f_note, fill=mix(BG, SHELF, g3), anchor="lm")


def s3(d, t):  # the instrument
    d.text((W // 2, 170), "The instrument", font=f_h2, fill=INK, anchor="mm")
    items = [("same question, two languages", "human-translated Hindi/English and Telugu/English pairs", SLATE, at("p3", "The same question")),
             ("same evidence, served three ways", "English-only · Indic-only · both  (frozen Wikipedia pool)", SHELF, at("p3", "The same evidence")),
             ("one agent, three searches, then an answer", "Gemini 2.5 Flash-Lite, 3.1 Flash-Lite, 3.6 Flash, Qwen3-30B", GOOD, at("p3", "A search agent")),
             ("every query logged by script", "then forced: match · english · dual", HOT, at("p3", "And a log"))]
    for i, (h, sub, col, ta) in enumerate(items):
        g = seg(t, ta, ta + 0.7)
        if g <= 0:
            continue
        y = 300 + i * 170
        d.rounded_rectangle([200, y, 1720, y + 130], radius=16, outline=mix(BG, col, g), width=4, fill=mix(BG, col, 0.05 * g))
        d.text((240, y + 42), h, font=f_lab, fill=mix(BG, col, g), anchor="lm"); d.text((240, y + 92), sub, font=f_note, fill=mix(BG, INK2, g), anchor="lm")


def s4(d, t):  # whose language
    d.text((W // 2, 170), "In whose language does the agent search?", font=f_h2, fill=INK, anchor="mm")
    d.text((W // 2, 240), "share of search queries written in English, free policy, Gemini 2.5 Flash-Lite", font=f_sub, fill=MUTED, anchor="mm")
    rows = [("Hindi question", cell("hi", "L|free|both", "latin_share"), HOT, at("p4", "thirty percent")),
            ("Telugu question", cell("te", "L|free|both", "latin_share"), SHELF, at("p4", "forty-four percent"))]
    bars(d, t, rows, y0=360, step=170, fmt="{:.0f}%")
    d.line([(160 + 550, 330), (160 + 550, 700)], fill=FAINT, width=3); d.text((160 + 550, 720), "half", font=f_note, fill=MUTED, anchor="mm")
    g = seg(t, at("p4", "And it does not"), at("p4", "And it does not") + 0.8)
    if g > 0:
        d.text((W // 2, 850), "and it does not change when the pool returns no Hindi text at all", font=f_body, fill=mix(BG, INK, g), anchor="mm")
        underline(d, 560, 1360, 875, seg(t, at("p4", "no Hindi text"), at("p4", "no Hindi text") + 0.7))


def s5(d, t):  # the gap
    d.text((W // 2, 170), "The gap", font=f_h2, fill=INK, anchor="mm")
    d.text((W // 2, 240), "evidence present in both languages, dense search, 287 Hindi items", font=f_sub, fill=MUTED, anchor="mm")
    rows = [("Hindi question", cell("hi", "L|free|both"), HOT, at("p5", "sixty-six percent")),
            ("English question", cell("hi", "en|free|both"), INK, at("p5", "seventy-six"))]
    bars(d, t, rows, y0=340, step=170)
    g = seg(t, at("p5", "Nine points"), at("p5", "Nine points") + 0.8)
    if g > 0:
        gap = FL["hi"]["contrasts"]["total_gap_free_both"]
        d.text((W // 2, 720), f"gap {100 * gap['delta']:.1f} points   [{100 * gap['ci'][0]:.1f}, {100 * gap['ci'][1]:.1f}]   survives correction", font=f_body, fill=mix(BG, HOT, g), anchor="mm")
    g2 = seg(t, at("p5", "For the two stronger"), at("p5", "For the two stronger") + 0.8)
    if g2 > 0:
        d.text((W // 2, 850), "Gemini 3.1 Flash-Lite: 3 points · Gemini 3.6 Flash: 2 points · inside the noise", font=f_lab, fill=mix(BG, MUTED, g2), anchor="mm")


def s6(d, t):  # the lever
    d.text((W // 2, 170), "Force the query language", font=f_h2, fill=INK, anchor="mm")
    d.text((W // 2, 240), "Hindi question, both pools, dense search: change in accuracy vs the free policy", font=f_sub, fill=MUTED, anchor="mm")
    con = FL["hi"]["contrasts"]
    rows = [("Hindi queries only", con["QG_recover_match"]["delta"], SHELF, at("p6", "Force the agent")),
            ("both languages", con["QG_recover_dual"]["delta"], GOOD, at("p6", "Force it to query")),
            ("English queries", con["QG_recover_english"]["delta"], SLATE, at("p6", "Force English"))]
    for i, (lab, val, col, ta) in enumerate(rows):
        y = 340 + i * 140; g = seg(t, ta, ta + 1.0)
        if g <= 0:
            continue
        d.text((160, y), lab, font=f_lab, fill=mix(BG, INK, min(1, g * 3)), anchor="lm")
        x0 = 760; d.line([(x0, y + 20), (x0, y + 90)], fill=FAINT, width=3)
        wv = int(900 * abs(val) * g)
        if wv > 2:
            d.rectangle([x0, y + 30, x0 + wv, y + 84] if val >= 0 else [x0 - wv, y + 30, x0, y + 84], fill=col)
        if g > 0.99:
            d.text((x0 + wv + 30 if val >= 0 else x0 - wv - 30, y + 57), f"{100 * val:+.1f}", font=f_mid, fill=col, anchor="lm" if val >= 0 else "rm")
    d.text((760, 790), "0", font=f_note, fill=MUTED, anchor="mm")
    g = seg(t, at("p6", "With a modern"), at("p6", "With a modern") + 0.8)
    if g > 0:
        d.text((W // 2, 880), "a Hindi query already finds the English passage: the query-side gap is almost nothing", font=f_body, fill=mix(BG, GOOD, g), anchor="mm")


def s7(d, t):  # swap retriever
    d.text((W // 2, 170), "Swap the search engine", font=f_h2, fill=SHELF, anchor="mm")
    d.text((W // 2, 240), "same model, same Hindi questions, keyword search (BM25) instead of dense", font=f_sub, fill=MUTED, anchor="mm")
    rows = [("English question", cell("hi", "en|free|both|bm25"), INK, at("p7", "the same model")),
            ("Hindi question, free", cell("hi", "L|free|both|bm25"), HOT, at("p7", "now lose")),
            ("Hindi queries only", cell("hi", "L|match|L|bm25"), SHELF, at("p7", "Searching only")),
            ("both languages", cell("hi", "L|dual|both|bm25"), GOOD, at("p7", "Searching in both"))]
    bars(d, t, rows, y0=320, step=130)
    g = seg(t, at("p7", "The query gap"), at("p7", "The query gap") + 0.8)
    if g > 0:
        d.text((W // 2, 900), "the query gap is a property of the search engine, not of the user", font=f_body, fill=mix(BG, SHELF, g), anchor="mm")
        underline(d, 420, 1500, 925, seg(t, at("p7", "not of the user"), at("p7", "not of the user") + 0.7), SHELF)


def s8(d, t):  # coverage
    d.text((W // 2, 170), "Does the Indic Wikipedia hold the answer?", font=f_h2, fill=INK, anchor="mm")
    d.text((W // 2, 240), "539 questions per language · string match, two independent LLM reads, manual audit", font=f_sub, fill=MUTED, anchor="mm")
    rows = [("Hindi article states the answer", FL["hi"]["coverage"]["cov_verified"], HOT, at("p8", "twenty-nine percent")),
            ("Telugu article states the answer", FL["te"]["coverage"]["cov_verified"], SHELF, at("p8", "twenty-four percent"))]
    bars(d, t, rows, y0=360, step=170, fmt="{:.0f}%")
    g = seg(t, at("p8", "Most of the evidence"), at("p8", "Most of the evidence") + 0.8)
    if g > 0:
        d.text((W // 2, 850), "most of the evidence an Indian user needs exists only in English", font=f_body, fill=mix(BG, INK, g), anchor="mm")


def s9(d, t):  # decomposition
    d.text((W // 2, 170), "A real Hindi user", font=f_h2, fill=INK, anchor="mm")
    d.text((W // 2, 240), "coverage-weighted expected accuracy, Gemini 2.5 Flash-Lite", font=f_sub, fill=MUTED, anchor="mm")
    db = FL["hi"]["decomposition_wild_bm25"]; dd = FL["hi"]["decomposition_wild"]
    rows = [("keyword search · English user", cell("hi", "en|free|en|bm25"), INK, at("p9", "seventy-one")),
            ("keyword search · Hindi user", db["free"]["acc_wild"], SHELF, at("p9", "forty-five percent")),
            ("keyword search · Hindi user, English queries", db["english"]["acc_wild"], GOOD, at("p9", "sixty-three")),
            ("cross-lingual search, measured · English user", FL["uncovered"]["hi"]["measured_decomposition"]["english_user_measured"], INK, at("p9", "for the English user")),
            ("cross-lingual search, measured · Hindi user", FL["uncovered"]["hi"]["measured_decomposition"]["free"]["measured_wild"], SLATE, at("p9", "the Hindi user gets"))]
    bars(d, t, rows, y0=300, step=125, w=1000)
    g = seg(t, at("p9", "harder for everyone"), at("p9", "harder for everyone") + 0.8)
    if g > 0:
        d.text((W // 2, 940), "the facts the Hindi Wikipedia lacks are harder for everyone; the gap stays nine points", font=f_lab, fill=mix(BG, SHELF, g), anchor="mm")


def s10(d, t):  # reading
    d.text((W // 2, 170), "What remains is reading", font=f_h2, fill=GOOD, anchor="mm")
    d.text((W // 2, 240), "the correct passage placed in the prompt, no search needed", font=f_sub, fill=MUTED, anchor="mm")
    rows = [("English question, English passage", cell("hi", "en|oracle_en|oracle"), INK, at("p10", "eighty-seven percent")),
            ("Hindi question, English passage", cell("hi", "L|oracle_en|oracle"), HOT, at("p10", "eighty-one")),
            ("Hindi question, Hindi passage", cell("hi", "L|oracle_L|oracle"), SHELF, at("p10", "seventy-three"))]
    bars(d, t, rows, y0=340, step=150)
    g = seg(t, at("p10", "Six points"), at("p10", "Six points") + 0.8)
    if g > 0:
        d.text((W // 2, 800), "six points with nothing left to retrieve", font=f_body, fill=mix(BG, HOT, g), anchor="mm")
        ring(d, 1370, 560, 150, seg(t, at("p10", "Six points"), at("p10", "Six points") + 0.9))
    g2 = seg(t, at("p10", "The cheap model"), at("p10", "The cheap model") + 0.8)
    if g2 > 0:
        d.text((W // 2, 900), "the cheap model reads English better than Hindi, even for a Hindi question", font=f_lab, fill=mix(BG, INK, g2), anchor="mm")


def s11(d, t):  # close
    d.text((W // 2, 200), "Six directions, written down first", font=f_h2, fill=INK, anchor="mm")
    g = seg(t, at("p11", "Three held"), at("p11", "Three held") + 1.0)
    if g > 0:
        for i, (lab, col) in enumerate([("held", GOOD), ("held", GOOD), ("held", GOOD), ("failed", HOT), ("failed", HOT), ("split", SHELF)]):
            x = 420 + i * 190
            d.rounded_rectangle([x, 300, x + 150, 380], radius=14, fill=mix(BG, col, 0.85 * g)); d.text((x + 75, 340), lab, font=f_lab, fill=mix(BG, BG, g), anchor="mm")
    g2 = seg(t, at("p11", "with a cross-lingual"), at("p11", "with a cross-lingual") + 0.8)
    if g2 > 0:
        wrap_text(d, "cross-lingual engine: the deficit is the model's reading, not the web and not the query", f_body, 300, 500, 1400, mix(BG, SLATE, g2), 46)
    g3 = seg(t, at("p11", "with a keyword"), at("p11", "with a keyword") + 0.8)
    if g3 > 0:
        wrap_text(d, "keyword engine: the deficit is the query, and the fix is to search in English", f_body, 300, 640, 1400, mix(BG, SHELF, g3), 46)
    g4 = seg(t, at("p11", "It depends"), at("p11", "It depends") + 0.8)
    if g4 > 0:
        d.text((W // 2, 820), "Search in whose language?", font=f_mid, fill=mix(BG, INK, g4), anchor="mm")
        d.text((W // 2, 900), "It depends on who is doing the searching.", font=f_body, fill=mix(BG, INK, g4), anchor="mm")
    g5 = seg(t, CUE["p11"]["start"] + CUE["p11"]["dur"] + 0.6, CUE["p11"]["start"] + CUE["p11"]["dur"] + 1.4)
    if g5 > 0:
        d.text((W // 2, 985), "Vizuara Research · abraar237.github.io/indic-search-gap", font=f_note, fill=mix(BG, MUTED, g5), anchor="mm")


SCENES = [("p1", s1), ("p2", s2), ("p3", s3), ("p4", s4), ("p5", s5), ("p6", s6), ("p7", s7), ("p8", s8), ("p9", s9), ("p10", s10), ("p11", s11)]


def bounds():
    out = []
    for i, (cue, fn) in enumerate(SCENES):
        a = cue_start(cue) - (0.35 if i else 0)
        b = cue_start(SCENES[i + 1][0]) - 0.35 if i + 1 < len(SCENES) else TOTAL + 1.0
        out.append((a, b, fn))
    return out


BOUNDS = None


def render_at(t):
    global BOUNDS
    if BOUNDS is None:
        BOUNDS = bounds()
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im); base(d, t)
    layers = [(min(seg(t, a - XFADE, a), 1 - seg(t, b, b + XFADE)), fn) for a, b, fn in BOUNDS if a - XFADE <= t < b + XFADE]
    for alpha, fn in layers:
        if alpha >= 0.999:
            fn(d, t)
        elif alpha > 0:
            im2 = Image.new("RGB", (W, H)); d2 = ImageDraw.Draw(im2); base(d2, t); fn(d2, t)
            im = Image.blend(im, im2, alpha); d = ImageDraw.Draw(im)
    return im


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        for a, b, fn in bounds():
            print(f"{fn.__name__}: {a:.1f}-{b:.1f}")
        for cue, fn in SCENES:
            render_at(cue_start(cue) + min(6.0, CUE[cue]["dur"] - 1)).save(HERE / f"_check_{cue}.png")
        print("anchors resolve; check frames written"); return
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()
    total = int((TOTAL + 1.5) * FPS)
    for f in range(total):
        render_at(f / FPS).save(FRAMES / f"f{f:06d}.png", compress_level=1)
        if f % 900 == 0:
            print(f"{f}/{total}", flush=True)
    print("frames done:", total)


if __name__ == "__main__":
    main()
