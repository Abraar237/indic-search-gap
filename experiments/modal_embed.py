"""Dense retriever arm: embed every pool chunk with BAAI/bge-m3 (dense, 1024-d, normalised) on Modal.

The big pools are NOT uploaded (local upstream bandwidth is ~0.5 MB/s). The Modal job downloads the same
wikipedia-monthly 20261001 parquet parts from Hugging Face and re-chunks them with the very same
build_corpus.chunk_article code, so chunk ids and order match the local corpus/pools/<lang>.jsonl exactly
(verified after the run by comparing the ids list). The small extras (en_extra.jsonl, gold_<lang>.jsonl)
are read from the Modal volume `indic-pools`, uploaded with `modal volume put`.

  python3 -m modal run experiments/modal_embed.py --lang hi
  python3 -m modal volume get indic-pools /emb/hi.fp16.npy corpus/emb/hi.fp16.npy
  python3 -m modal volume get indic-pools /emb/hi.ids.json corpus/emb/hi.ids.json
"""
import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("sentence-transformers==5.1.0", "torch==2.8.0", "numpy", "pyarrow", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .add_local_file("experiments/build_corpus.py", "/root/build_corpus.py")
)
vol = modal.Volume.from_name("indic-pools", create_if_missing=True)
hf = modal.Volume.from_name("indic-hf-cache", create_if_missing=True)
app = modal.App("indic-embed")
EN_PARTS = 26


@app.function(image=image, gpu="A100-40GB", timeout=4 * 60 * 60, cpu=8, memory=65536,
              volumes={"/data": vol, "/root/.cache/huggingface": hf})
def embed(lang: str, batch: int = 256):
    import glob, json, os, sys, time
    import numpy as np
    import torch
    sys.path.insert(0, "/root")
    from build_corpus import chunk_article
    from huggingface_hub import snapshot_download
    import pyarrow.parquet as pq

    if lang == "en":
        pats = [f"20261001/en/train/train_part_{i:03d}.parquet" for i in range(EN_PARTS)]
    else:
        pats = [f"20261001/{lang}/train/*.parquet"]
    root = snapshot_download("omarkamali/wikipedia-monthly", repo_type="dataset", allow_patterns=pats,
                             local_dir="/root/.cache/huggingface/wm", max_workers=8)
    files = sorted(glob.glob(f"{root}/20261001/{lang}/train/*.parquet"))
    ids, texts = [], []
    for fp in files:
        t = pq.read_table(fp, columns=["id", "title", "text"])
        for aid, title, text in zip(t["id"].to_pylist(), t["title"].to_pylist(), t["text"].to_pylist()):
            if not text or not title:
                continue
            for k, c in enumerate(chunk_article(title, text)):
                ids.append(f"{lang}:{aid}:{k}"); texts.append(c)
    n_main = len(texts)
    for extra in (f"/data/{lang}_extra.jsonl", f"/data/gold_{lang}.jsonl"):
        if os.path.exists(extra):
            with open(extra) as f:
                for line in f:
                    r = json.loads(line)
                    ids.append(r["id"]); texts.append(r["text"])
    print(lang, "main chunks", n_main, "total", len(texts), "files", len(files), flush=True)
    model = SentenceTransformer = __import__("sentence_transformers").SentenceTransformer
    model = SentenceTransformer("BAAI/bge-m3", device="cuda", model_kwargs={"torch_dtype": torch.float16})
    model.max_seq_length = 512
    t0 = time.time()
    out = np.zeros((len(texts), 1024), dtype=np.float16)
    step = 32768
    for i in range(0, len(texts), step):
        e = model.encode([t[:2000] for t in texts[i:i + step]], batch_size=batch, normalize_embeddings=True,
                         convert_to_numpy=True, show_progress_bar=False)
        out[i:i + step] = e.astype(np.float16)
        print(f"  {min(i + step, len(texts))}/{len(texts)} {time.time() - t0:.0f}s", flush=True)
    os.makedirs("/data/emb", exist_ok=True)
    np.save(f"/data/emb/{lang}.fp16.npy", out)
    json.dump(ids, open(f"/data/emb/{lang}.ids.json", "w"))
    vol.commit()
    return {"lang": lang, "n": len(texts), "n_main": n_main, "seconds": round(time.time() - t0)}


@app.local_entrypoint()
def main(lang: str = "hi"):
    print(embed.remote(lang))
