#!/usr/bin/env python3
"""BM25 indexes over the evidence pools (bm25s), one per served-pool condition.

  python3 index.py build            -> corpus/index/{en,hi,te,hi+en,te+en}/
  python3 index.py query <pool> "<query>" [k]

Gold passages from corpus/items.json are injected as extra chunks (ids "<lang>:gold:<item_id>")
so every item's evidence is guaranteed present in the pool of its language. Tokeniser: NFC,
lowercase, Unicode word characters; English stopwords removed from en text only; no stemming
(Indic morphology is left intact; a known limitation reported in the paper).
"""
import json
import pathlib
import re
import sys
import unicodedata

import bm25s

ROOT = pathlib.Path(__file__).resolve().parent.parent
POOLS = ROOT / "corpus" / "pools"
INDEX = ROOT / "corpus" / "index"
ITEMS = ROOT / "corpus" / "items.json"
COMBOS = {"en": ["en"], "hi": ["hi"], "te": ["te"], "hi+en": ["hi", "en"], "te+en": ["te", "en"]}
EN_STOP = set("a an the of in on at to for and or is are was were be been by with as from that this these those it its into than then there their they he she his her which who whom what when where why how not no do does did has have had can could will would may might shall should about over under between also such other more most some any each".split())
WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text, lang=None):
    """NFC, lowercase, Unicode word tokens; English stopwords removed from EVERY document and query (Latin
    snippets inside Indic articles would otherwise match query stopwords); no stemming."""
    s = unicodedata.normalize("NFC", text).lower()
    return [t for t in WORD.findall(s) if t not in EN_STOP]


def gold_chunks(lang):
    if not ITEMS.exists():
        return []
    out, seen = [], set()   # XorQA hi and te items share one English passage: inject it once
    for it in json.load(open(ITEMS))["items"]:
        if lang == "en" and it.get("gold_en") and it["gold_en"] not in seen:
            seen.add(it["gold_en"])
            out.append({"id": f"en:gold:{it['id']}", "lang": "en", "title": it.get("en_title") or "", "k": -1,
                        "text": (it.get("en_title") or "") + "\n" + it["gold_en"]})
        if lang == it["lang"] and it.get("gold_L") and it["gold_L"] not in seen:
            seen.add(it["gold_L"])
            out.append({"id": f"{lang}:gold:{it['id']}", "lang": lang, "title": it.get("L_title") or "", "k": -1,
                        "text": (it.get("L_title") or "") + "\n" + it["gold_L"]})
    return out


def load_pool(lang):
    docs = []
    with open(POOLS / f"{lang}.jsonl") as f:
        for line in f:
            docs.append(json.loads(line))
    extra = POOLS / f"{lang}_extra.jsonl"
    if extra.exists():
        with open(extra) as f:
            for line in f:
                docs.append(json.loads(line))
    docs += gold_chunks(lang)
    return docs


def build(name):
    langs = COMBOS[name]
    docs = []
    for l in langs:
        docs += load_pool(l)
    print(f"{name}: {len(docs)} chunks; tokenising", flush=True)
    corpus_tokens = [tokenize(d["text"], d["lang"]) for d in docs]
    retriever = bm25s.BM25(k1=1.2, b=0.75)
    retriever.index(corpus_tokens)
    out = INDEX / name
    out.mkdir(parents=True, exist_ok=True)
    retriever.save(str(out))
    with open(out / "docs.jsonl", "w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"{name}: saved to {out}", flush=True)


class Searcher:
    """Memory-light: the BM25 matrices are mmapped and passages are read from docs.jsonl by byte offset
    (offsets cached in offsets.npy), so a 1.6M-passage pool costs ~15 MB of RAM instead of ~3 GB."""

    def __init__(self, name):
        import numpy as np
        self.name = name
        self.retriever = bm25s.BM25.load(str(INDEX / name), mmap=True)
        self.path = INDEX / name / "docs.jsonl"
        off = INDEX / name / "offsets.npy"
        if not off.exists():
            offs, pos = [], 0
            with open(self.path, "rb") as f:
                for line in f:
                    offs.append(pos)
                    pos += len(line)
            np.save(off, np.asarray(offs, dtype=np.int64))
        self.offsets = np.load(off)
        self.n = len(self.offsets)
        self.fh = open(self.path, "rb")

    def doc(self, i):
        self.fh.seek(int(self.offsets[i]))
        return json.loads(self.fh.readline())

    def search(self, query, k=5, exclude_ids=()):
        q = tokenize(query, None)
        if not q:
            return []
        kk = k + len(exclude_ids) + 5
        res, scores = self.retriever.retrieve([q], k=min(kk, self.n), show_progress=False)
        out = []
        for i, s in zip(res[0], scores[0]):
            d = self.doc(int(i))
            if d["id"] in exclude_ids or float(s) <= 0:
                continue
            out.append({"id": d["id"], "lang": d["lang"], "title": d["title"], "text": d["text"], "score": round(float(s), 3)})
            if len(out) >= k:
                break
        return out


class DenseSearcher:
    """bge-m3 dense retrieval over corpus/emb/<lang>.fp16.npy (+ ids). Exact inner-product search as a torch
    fp16 matmul on the Apple GPU (MPS) when available, else chunked float32 on CPU. FAISS is deliberately not
    used: its bundled OpenMP runtime conflicts with PyTorch's on macOS (crash / deadlock)."""
    _model = None

    def __init__(self, name):
        import numpy as np
        import torch
        self.name = name
        self.ids, mats = [], []
        for lang in COMBOS[name]:
            self.ids += json.load(open(ROOT / "corpus" / "emb" / f"{lang}.ids.json"))
            mats.append(np.load(ROOT / "corpus" / "emb" / f"{lang}.fp16.npy", mmap_mode="r"))
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        n = sum(m.shape[0] for m in mats)
        # copy part by part so the CPU never holds more than one pool's fp16 matrix (peak RAM ~2 GB, not 8)
        self.E = torch.empty((n, 1024), dtype=torch.float16, device=self.device)
        off = 0
        for m in mats:
            step = 131072
            for i in range(0, m.shape[0], step):
                blk = torch.from_numpy(np.ascontiguousarray(m[i:i + step]))
                self.E[off + i:off + i + blk.shape[0]] = blk.to(self.device)
                del blk
            off += m.shape[0]
        del mats
        import gc
        gc.collect()
        self.n = self.E.shape[0]
        assert self.n == len(self.ids), (self.n, len(self.ids))
        self.docs = DocStore(name)

    @classmethod
    def model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer("BAAI/bge-m3", device="cpu")
            cls._model.max_seq_length = 128
        return cls._model

    def _scores(self, q):
        import torch
        if self.device == "mps":
            qt = torch.from_numpy(q).to("mps", dtype=torch.float16)
            return (self.E @ qt).float().cpu()
        qt = torch.from_numpy(q)
        out = torch.empty(self.n)
        step = 262144
        for i in range(0, self.n, step):
            out[i:i + step] = self.E[i:i + step].float() @ qt
        return out

    def search(self, query, k=5, exclude_ids=()):
        import numpy as np
        import torch
        q = self.model().encode([query], normalize_embeddings=True, convert_to_numpy=True)[0].astype(np.float32)
        sc = self._scores(q)
        kk = min(k + len(exclude_ids) + 5, self.n)
        vals, idx = torch.topk(sc, kk)
        out = []
        for s, i in zip(vals.tolist(), idx.tolist()):
            cid = self.ids[i]
            if cid in exclude_ids:
                continue
            d = self.docs.get(cid)
            if d is None:
                continue
            out.append({"id": d["id"], "lang": d["lang"], "title": d["title"], "text": d["text"], "score": round(float(s), 4)})
            if len(out) >= k:
                break
        return out


class DocStore:
    """chunk id -> passage, by byte offset into the BM25 index's docs.jsonl (same docs as BM25)."""

    def __init__(self, name):
        import numpy as np
        self.path = INDEX / name / "docs.jsonl"
        idmap = INDEX / name / "idmap.json"
        if not idmap.exists():
            m, pos = {}, 0
            with open(self.path, "rb") as f:
                for line in f:
                    m[json.loads(line)["id"]] = pos
                    pos += len(line)
            json.dump(m, open(idmap, "w"))
        self.pos = json.load(open(idmap))
        self.fh = open(self.path, "rb")

    def get(self, cid):
        p = self.pos.get(cid)
        if p is None:
            return None
        self.fh.seek(p)
        return json.loads(self.fh.readline())


class HybridSearcher:
    """Reciprocal-rank fusion of BM25 and dense (k=60), top-50 each -> top-k. The main-grid retriever."""

    def __init__(self, name):
        self.name = name
        self.bm25 = Searcher(name)
        self.dense = DenseSearcher(name)

    def search(self, query, k=5, exclude_ids=()):
        a = self.bm25.search(query, 50, exclude_ids)
        b = self.dense.search(query, 50, exclude_ids)
        score, seen = {}, {}
        for lst in (a, b):
            for r, h in enumerate(lst):
                score[h["id"]] = score.get(h["id"], 0.0) + 1.0 / (60 + r + 1)
                seen[h["id"]] = h
        top = sorted(score, key=lambda i: -score[i])[:k]
        out = []
        for i in top:
            h = dict(seen[i]); h["score"] = round(score[i], 5); out.append(h)
        return out


def make_searcher(name, retriever="hybrid"):
    return {"bm25": Searcher, "dense": DenseSearcher, "hybrid": HybridSearcher}[retriever](name)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        for name in (sys.argv[2:] or list(COMBOS)):
            build(name)
    elif cmd == "query":
        s = Searcher(sys.argv[2])
        for r in s.search(sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 5):
            print(r["score"], r["id"], r["title"], "|", r["text"][:160].replace("\n", " "))
