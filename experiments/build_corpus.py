#!/usr/bin/env python3
"""Build the evidence pools from the wikipedia-monthly 20261001 snapshot.

  python3 build_corpus.py pools      -> corpus/pools/{hi,te,en}.jsonl  (chunked articles)
  python3 build_corpus.py stats      -> prints pool sizes

Chunking: split article text on blank lines / newlines into paragraphs, merge paragraphs
until ~CHUNK_CHARS, prefix every chunk with the article title so lexical search can hit the
entity name. Cap chunks per article (long English articles) at MAX_CHUNKS.
Deterministic; chunk ids are "<lang>:<article_id>:<k>".
"""
import glob
import json
import os
import pathlib
import re
import sys

import pyarrow.parquet as pq

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw" / "wiki" / "20261001"
POOLS = ROOT / "corpus" / "pools"
POOLS.mkdir(parents=True, exist_ok=True)
CHUNK_CHARS = 900          # ~150 English words; Indic scripts have longer char/word ratios
MIN_CHUNK_CHARS = 120
MAX_CHUNKS = 12
LANGS = ["hi", "te", "en"]


def paragraphs(text):
    text = re.sub(r"\r", "", text)
    for p in re.split(r"\n\s*\n|\n", text):
        p = p.strip()
        if len(p) >= 20:
            yield p


def chunk_article(title, text):
    out, buf = [], ""
    for p in paragraphs(text):
        if len(buf) + len(p) + 1 > CHUNK_CHARS and buf:
            out.append(buf)
            buf = p
        else:
            buf = (buf + "\n" + p) if buf else p
        if len(out) >= MAX_CHUNKS:
            break
    if buf and len(out) < MAX_CHUNKS:
        out.append(buf)
    out = [c for c in out if len(c) >= MIN_CHUNK_CHARS]
    return [f"{title}\n{c}" for c in out]


def build(lang):
    files = sorted(glob.glob(str(RAW / lang / "train" / "*.parquet")))
    out = POOLS / f"{lang}.jsonl"
    n_art = n_chunk = 0
    with open(out, "w") as f:
        for fp in files:
            t = pq.read_table(fp, columns=["id", "title", "text"])
            for aid, title, text in zip(t["id"].to_pylist(), t["title"].to_pylist(), t["text"].to_pylist()):
                if not text or not title:
                    continue
                chunks = chunk_article(title, text)
                if not chunks:
                    continue
                n_art += 1
                for k, c in enumerate(chunks):
                    f.write(json.dumps({"id": f"{lang}:{aid}:{k}", "lang": lang, "title": title, "k": k, "text": c},
                                       ensure_ascii=False) + "\n")
                    n_chunk += 1
            print(f"  {lang} {os.path.basename(fp)} articles={n_art} chunks={n_chunk}", flush=True)
    print(f"{lang}: {n_art} articles, {n_chunk} chunks -> {out}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pools"
    if cmd == "pools":
        for lang in (sys.argv[2:] or LANGS):
            build(lang)
    elif cmd == "stats":
        for lang in LANGS:
            p = POOLS / f"{lang}.jsonl"
            if p.exists():
                n = sum(1 for _ in open(p))
                print(lang, n, "chunks", round(p.stat().st_size / 1e6, 1), "MB")
