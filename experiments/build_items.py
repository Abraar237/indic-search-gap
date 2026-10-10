#!/usr/bin/env python3
"""Build the question bank: corpus/items.json.

Sources (all parallel en/L with gold answers):
  A. IndicGenBench XorQA-In test (539 items; hi, te, en questions aligned by index; English gold
     passage given; Indic gold answers in `translated_answers`). The Indic Wikipedia counterpart
     of the English article is located through Wikidata sitelinks (corpus/meta/sitelinks.json) and
     the 20261001 snapshot; coverage = the Indic answer string (or the English answer string)
     occurs in that article's text.
  B. MLQA hi (4,918 hi questions with the same ids in the en-en file): natively parallel
     Wikipedia paragraphs in both languages -> evidence in BOTH by construction (both gold
     paragraphs are injected into the pools as extra chunks).
  C. tydi_xor_rc te validation (291 answerable): natively written Telugu questions with an English
     gold passage; no English question -> Q=te-only robustness subset (translation-artefact check).
  D. IndicQuest-v2 (3,471 parallel en/hi/te India-centric closed-book items): added by
     build_items.py indicquest AFTER the BM25 indexes exist (evidence located by answer search).

Writes corpus/items.json; every item carries: id, source, lang (the Indic language), q_en, q_L,
ans_en (list), ans_L (list), gold_en (text or None), gold_L (text or None), en_title, L_title,
cov_L_article (bool: an L article exists), cov_L_answer (bool: answer string found in L article).
"""
import json
import pathlib
import random
import re
import sys
import unicodedata

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw"
META = ROOT / "corpus" / "meta"
POOLS = ROOT / "corpus" / "pools"
OUT = ROOT / "corpus" / "items.json"
random.seed(7)


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    s = s.lower()
    s = re.sub(r"[।॥.,;:!?\"'()\[\]{}«»“”‘’\-–—/]", " ", s)
    return " ".join(s.split())


CHUNKS = {}


def load_article_text(lang, titles_needed):
    """Return {title: full_text} for the needed titles from the chunked pool (chunks concatenated).
    Also keeps the chunks themselves in CHUNKS[lang][title] = [(k, id, text)] for gold-chunk location."""
    want = set(titles_needed)
    found = {}
    CHUNKS[lang] = {}
    with open(POOLS / f"{lang}.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if r["title"] in want:
                body = r["text"].split("\n", 1)[1] if "\n" in r["text"] else r["text"]
                found.setdefault(r["title"], []).append((r["k"], body))
                CHUNKS[lang].setdefault(r["title"], []).append((r["k"], r["id"], r["text"]))
    return {t: "\n".join(x[1] for x in sorted(v)) for t, v in found.items()}


def locate_gold_chunk(lang, title, answers):
    for k, cid, text in sorted(CHUNKS.get(lang, {}).get(title, [])):
        if answer_in(text, answers):
            return cid, text
    return None, None


def answer_in(text, answers):
    nt = norm(text)
    return any(norm(a) and norm(a) in nt for a in answers)


def build_xorqa():
    sl = json.load(open(META / "sitelinks.json"))
    ex = {l: json.load(open(RAW / "indicgenbench" / f"xorqa_{l}_test.json"))["examples"] for l in ("hi", "te", "en")}
    items = []
    for lang in ("hi", "te"):
        site = {"hi": "hiwiki", "te": "tewiki"}[lang]
        titles = []
        for e in ex["en"]:
            t = e["title"].split("_parentSection:")[0].replace("title:", "", 1)
            titles.append(sl.get(t, {}).get(site))
        texts = load_article_text(lang, [t for t in titles if t])
        for i, (e_en, e_l) in enumerate(zip(ex["en"], ex[lang])):
            assert e_en["context"] == e_l["context"]
            en_title = e_en["title"].split("_parentSection:")[0].replace("title:", "", 1)
            l_title = titles[i]
            ans_en = sorted({a["text"] for a in e_en["answers"] if a["text"].strip()})
            # 237 of 539 Telugu items carry the garbage translation "అని" ("that") as the answer; drop such
            # function-word answers (<= 3 chars and not a number) so they cannot match or be judged correct.
            ans_l = sorted({a["text"].strip() for a in e_l["translated_answers"]
                            if a["text"].strip() and (len(a["text"].strip()) > 3 or a["text"].strip().isdigit()) and a["text"].strip() != "అని"})
            art = texts.get(l_title) if l_title else None
            cov = bool(art) and answer_in(art, ans_l + ans_en)
            gcid, gtext = locate_gold_chunk(lang, l_title, ans_l + ans_en) if cov else (None, None)
            items.append({
                "gold_L_chunk_id": gcid, "gold_L": gtext.split("\n", 1)[1] if gtext and "\n" in gtext else gtext,
                "factorial": cov,
                "id": f"xorqa_{lang}_{i:03d}", "source": "xorqa_in", "lang": lang,
                "q_en": e_en["question"], "q_L": e_l["question"],
                "ans_en": ans_en, "ans_L": ans_l,
                "gold_en": e_en["context"],
                "en_title": en_title, "L_title": l_title,
                "cov_L_article": art is not None,
                "cov_L_answer": cov,
                "L_article_chars": len(art) if art else 0,
            })
    return items


def build_mlqa(n_per=130):
    def flat(d):
        out = {}
        for a in d["data"]:
            for p in a["paragraphs"]:
                for q in p["qas"]:
                    out[q["id"]] = {"title": a["title"], "ctx": p["context"], "q": q["question"],
                                    "ans": sorted({x["text"] for x in q["answers"]})}
        return out
    H = flat(json.load(open(RAW / "mlqa" / "MLQA_V1" / "test" / "test-context-hi-question-hi.json")))
    E = flat(json.load(open(RAW / "mlqa" / "MLQA_V1" / "test" / "test-context-en-question-en.json")))
    ids = sorted(set(H) & set(E))
    rng = random.Random(11)
    rng.shuffle(ids)
    # keep only questions judged self-contained (corpus/meta/mlqa_selfcontained.json, LLM filter, stage "filter");
    # the pilot showed that many MLQA questions presuppose their paragraph.
    sc = json.load(open(META / "mlqa_selfcontained.json"))
    ids = [k for k in ids if sc.get(k, {}).get("ok")]
    items = []
    for k in ids[:n_per]:
        h, e = H[k], E[k]
        items.append({
            "id": f"mlqa_hi_{k[:12]}", "source": "mlqa", "lang": "hi",
            "q_en": e["q"], "q_L": h["q"], "ans_en": e["ans"], "ans_L": h["ans"],
            "gold_en": e["ctx"], "gold_L": h["ctx"], "en_title": e["title"], "L_title": h["title"],
            "cov_L_article": True, "cov_L_answer": True, "L_article_chars": len(h["ctx"]),
            "gold_L_chunk_id": None, "factorial": True,
        })
    return items


def build_tydi_te(n=120):
    df = pd.read_parquet(RAW / "xor_tydi" / "validation.parquet")
    df = df[(df.lang == "te") & (df.answerable == True)].reset_index(drop=True)
    rng = random.Random(5)
    idx = list(range(len(df)))
    rng.shuffle(idx)
    items = []
    for i in idx[:n]:
        r = df.iloc[i]
        ans_en = [str(r["answer"])]
        ans_l = [str(r["answer_inlang"])] if isinstance(r["answer_inlang"], str) and r["answer_inlang"].strip() else []
        items.append({
            "id": f"tydi_te_{i:03d}", "source": "tydi_xor_rc", "lang": "te",
            "q_en": None, "q_L": r["question"], "ans_en": ans_en, "ans_L": ans_l,
            "gold_en": r["context"], "gold_L": None, "en_title": None, "L_title": None,
            "cov_L_article": None, "cov_L_answer": None, "L_article_chars": 0,
            "gold_L_chunk_id": None, "factorial": False,
        })
    return items


if __name__ == "__main__":
    items = build_xorqa() + build_mlqa() + build_tydi_te()
    json.dump({"snapshot": "omarkamali/wikipedia-monthly 20261001", "n": len(items), "items": items},
              open(OUT, "w"), ensure_ascii=False, indent=0)
    df = pd.DataFrame(items)
    print(df.groupby(["source", "lang"]).size())
    x = df[df.source == "xorqa_in"]
    print(x.groupby("lang")[["cov_L_article", "cov_L_answer"]].mean().round(3))
    print("xorqa items with L article but answer not found:", int(((x.cov_L_article) & (~x.cov_L_answer)).sum()))
