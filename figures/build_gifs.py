#!/usr/bin/env python3
"""Three concept GIFs in the clean flat chart style (white card, flat bars, thin rules, monospace numerals,
replay pill, Helvetica): 840x840, 80 ms/frame, numbers from results/analysis.json (Gemini 2.5 Flash-Lite,
the model with the full grid). Also writes an MP4 of each for LinkedIn."""
import json, math, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "docs" / "assets" / "gifs"
OUT.mkdir(parents=True, exist_ok=True)
A = json.load(open(ROOT / "results" / "analysis.json"))
M = A["models"]["google/gemini-2.5-flash-lite"]
W = H = 840
INK = (22, 19, 13); INK2 = (58, 53, 43); MUTED = (109, 102, 90); FAINT = (164, 156, 140); RULE = (231, 226, 213)
BG = (253, 252, 250); SLATE = (21, 94, 140); HOT = (179, 0, 107); SHELF = (192, 100, 26); GOOD = (28, 122, 85)
MENLO = "/System/Library/Fonts/Menlo.ttc"; HELV = "/System/Library/Fonts/Helvetica.ttc"
F = lambda p, s, i=0: ImageFont.truetype(p, s, index=i)
f_title = F(MENLO, 30, 1); f_sub = F(HELV, 15); f_note = F(HELV, 13); f_label = F(HELV, 17); f_num = F(MENLO, 22); f_big = F(MENLO, 44, 1); f_mono = F(MENLO, 16)
N_FRAMES, HOLD = 70, 22


def ease(t):
    return 0 if t <= 0 else 1 if t >= 1 else 0.5 - 0.5 * math.cos(math.pi * t)


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else 1.0


def card(d):
    d.rectangle([0, 0, W, H], fill=BG); d.rectangle([14, 14, W - 14, H - 14], outline=RULE, width=2)


def title_block(d, title, sub):
    d.text((W // 2, 62), title, font=f_title, fill=INK, anchor="mm"); d.text((W // 2, 96), sub.upper(), font=f_sub, fill=MUTED, anchor="mm")


def footer(d, text):
    d.text((W // 2, H - 44), text.upper(), font=f_note, fill=FAINT, anchor="mm")


def replay(d, t):
    x, y = W - 120, H - 78
    d.rounded_rectangle([x, y, x + 86, y + 28], radius=14, outline=RULE, width=2, fill=BG if t < 0.97 else RULE)
    d.text((x + 43, y + 14), "replay", font=f_note, fill=MUTED, anchor="mm")


def hbar(d, x, y, w, h, frac, color, label, value, t_label=1.0):
    d.text((x - 14, y + h / 2), label, font=f_label, fill=INK2, anchor="rm")
    d.rectangle([x, y, x + w, y + h], outline=RULE, width=2)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 4:
        d.rectangle([x + 2, y + 2, x + fw - 2, y + h - 2], fill=color)
    if t_label > 0.5:
        d.text((x + w + 12, y + h / 2), value, font=f_num, fill=INK, anchor="lm")


def save(frames, name):
    frames[0].save(OUT / f"{name}.gif", save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)
    mp4 = OUT / f"{name}.mp4"
    tmp = OUT / f"_{name}_%03d.png"
    for i, fr in enumerate(frames):
        fr.save(str(tmp) % i)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12.5", "-i", str(tmp), "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20", str(mp4)], check=True)
    for p in OUT.glob(f"_{name}_*.png"):
        p.unlink()
    print(name, len(frames), "frames,", (OUT / f"{name}.gif").stat().st_size // 1024, "KB")


def cell(lang, k):
    return M[lang]["cells"].get(k, {})


def gif1():
    """In whose language does the agent search? English-query share under the free policy."""
    rows = [("Hindi question, English-only pool", cell("hi", "L|free|en")["latin_share"], HOT),
            ("Hindi question, both pools", cell("hi", "L|free|both")["latin_share"], HOT),
            ("Hindi question, Hindi-only pool", cell("hi", "L|free|L")["latin_share"], HOT),
            ("Telugu question, English-only pool", cell("te", "L|free|en")["latin_share"], SHELF),
            ("Telugu question, both pools", cell("te", "L|free|both")["latin_share"], SHELF),
            ("Telugu question, Telugu-only pool", cell("te", "L|free|L")["latin_share"], SHELF)]
    frames = []
    for i in range(N_FRAMES + HOLD):
        t = min(1.0, i / N_FRAMES)
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); card(d)
        title_block(d, "Search in whose language?", "share of search queries written in English, free policy")
        x, w = 330, 330
        for r, (lab, v, col) in enumerate(rows):
            y = 170 + r * 92
            tt = seg(t, 0.08 + r * 0.1, 0.38 + r * 0.1)
            hbar(d, x, y, w, 44, v * tt, col, lab, f"{100 * v:.0f}%", tt)
        d.line([x + w // 2, 150, x + w // 2, 720], fill=FAINT, width=2)
        d.text((x + w // 2, 735), "half", font=f_note, fill=MUTED, anchor="mm")
        d.text((W // 2, 772), "the agent chose the language itself; it does not switch when a pool returns no Indic text", font=f_note, fill=MUTED, anchor="mm")
        footer(d, "Gemini 2.5 Flash-Lite · 287 Hindi and 127 Telugu questions · bge-m3 search")
        replay(d, t); frames.append(im)
    save(frames, "whose-language")


def gif2():
    """Lexical vs cross-lingual search: the Hindi user's accuracy and what searching in English recovers."""
    rows = [("English user", cell("hi", "en|free|en|bm25")["acc"], cell("hi", "en|free|en")["acc"]),
            ("Hindi user, free policy", M["hi"]["decomposition_wild_bm25"]["free"]["acc_wild"], M["hi"]["decomposition_wild"]["free"]["acc_wild"]),
            ("Hindi user, English queries", M["hi"]["decomposition_wild_bm25"]["english"]["acc_wild"], M["hi"]["decomposition_wild"]["english"]["acc_wild"]),
            ("Hindi user, Hindi queries only", M["hi"]["decomposition_wild_bm25"]["match"]["acc_wild"], M["hi"]["decomposition_wild"]["match"]["acc_wild"])]
    frames = []
    for i in range(N_FRAMES + HOLD):
        t = min(1.0, i / N_FRAMES)
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); card(d)
        title_block(d, "The query gap belongs to the engine", "expected accuracy of a real user, two kinds of search")
        d.text((330 + 80, 150), "LEXICAL (BM25)", font=f_sub, fill=MUTED, anchor="mm")
        d.text((330 + 80, 450), "CROSS-LINGUAL (bge-m3)", font=f_sub, fill=MUTED, anchor="mm")
        x, w = 330, 300
        for r, (lab, vb, vd) in enumerate(rows):
            tb = seg(t, 0.05 + r * 0.08, 0.35 + r * 0.08); td = seg(t, 0.45 + r * 0.08, 0.75 + r * 0.08)
            hbar(d, x, 175 + r * 60, w, 40, vb * tb, SHELF if r else INK, lab, f"{100 * vb:.0f}", tb)
            hbar(d, x, 475 + r * 60, w, 40, vd * td, SLATE if r else INK, lab, f"{100 * vd:.0f}", td)
        d.text((W // 2, 740), "with lexical search the Hindi user loses 26 points and English queries win 18 back;", font=f_note, fill=MUTED, anchor="mm")
        d.text((W // 2, 760), "with cross-lingual search the query language stops mattering", font=f_note, fill=MUTED, anchor="mm")
        footer(d, "Gemini 2.5 Flash-Lite · coverage-weighted extrapolation from the covered items · Hindi")
        replay(d, t); frames.append(im)
    save(frames, "engine-not-query")


def gif3():
    """What is left: the integration gap. Closed-book, search, oracle passage, English question."""
    rows = [("knows it closed-book", cell("hi", "L|closed|closed")["acc"], FAINT),
            ("Hindi question, search", cell("hi", "L|free|both")["acc"], SLATE),
            ("Hindi question, passage given", cell("hi", "L|oracle_en|oracle")["acc"], GOOD),
            ("English question, search", cell("hi", "en|free|both")["acc"], INK),
            ("English question, passage given", cell("hi", "en|oracle_en|oracle")["acc"], INK)]
    frames = []
    for i in range(N_FRAMES + HOLD):
        t = min(1.0, i / N_FRAMES)
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); card(d)
        title_block(d, "What remains is reading, not the web", "Hindi questions, evidence present in both languages")
        x, w = 360, 320
        for r, (lab, v, col) in enumerate(rows):
            tt = seg(t, 0.08 + r * 0.11, 0.4 + r * 0.11)
            hbar(d, x, 190 + r * 90, w, 46, v * tt, col, lab, f"{100 * v:.0f}", tt)
        gap = cell("hi", "en|oracle_en|oracle")["acc"] - cell("hi", "L|oracle_en|oracle")["acc"]
        if t > 0.9:
            d.text((W // 2, 690), f"same passage in front of the model: the Hindi question still answers {100 * gap:.0f} points worse", font=f_note, fill=HOT, anchor="mm")
        d.text((W // 2, 740), "the served pool language changed nothing; the model's reading did", font=f_note, fill=MUTED, anchor="mm")
        footer(d, "Gemini 2.5 Flash-Lite · 287 Hindi questions · bge-m3 search")
        replay(d, t); frames.append(im)
    save(frames, "reading-not-web")


if __name__ == "__main__":
    gif1(); gif2(); gif3()
