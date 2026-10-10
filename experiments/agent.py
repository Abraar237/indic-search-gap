"""The search agent: a fixed ReAct loop over OpenRouter tool calling.

run_episode(model, item, qlang, policy, pool, searcher, key, ...) -> record dict
  qlang  : "en" or the item's Indic language code (which question text is asked)
  policy : free | match | english | dual   (see prompts.py)
  pool   : the Searcher serving one evidence condition (en, hi, te, hi+en, te+en) or None (closed-book)
Logs every search call with the query, its detected script, the hit ids, and whether a gold chunk
was hit; the final answer; token usage and exact cost. Temperature 0, reasoning effort minimal.
"""
import json
import pathlib
import random
import re
import time
import unicodedata
import urllib.error
import urllib.request

import cost_tracker
from prompts import LANG_NAME, NO_RESULTS, POLICY, SYSTEM_AGENT, SYSTEM_CLOSED, SYSTEM_ORACLE, TOOL_SEARCH, USER_ORACLE

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://openrouter.ai/api/v1/chat/completions"
K = 5
MAX_SEARCHES = 3
MAX_TOKENS_STEP = 500
MAX_TOKENS_FINAL = 200


def env(key):
    for line in open(ROOT / ".env"):
        if line.startswith(key + "="):
            return line.strip().split("=", 1)[1]
    raise KeyError(key)


def script_of(text):
    """Dominant script of a query: Deva, Telu, Beng, Taml, Latn, Mixed, Other."""
    counts = {"Deva": 0, "Telu": 0, "Beng": 0, "Taml": 0, "Latn": 0}
    for ch in text:
        if not ch.isalpha():
            continue
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            counts["Deva"] += 1
        elif 0x0C00 <= o <= 0x0C7F:
            counts["Telu"] += 1
        elif 0x0980 <= o <= 0x09FF:
            counts["Beng"] += 1
        elif 0x0B80 <= o <= 0x0BFF:
            counts["Taml"] += 1
        elif ch.isascii():
            counts["Latn"] += 1
    tot = sum(counts.values())
    if tot == 0:
        return "Other"
    top, n = max(counts.items(), key=lambda x: x[1])
    return top if n / tot >= 0.8 else "Mixed"


def post(body, key, tries=6):
    """OpenRouter by default; models named "modal/<served-name>" go to the vLLM endpoint in MODAL_VLLM_URL
    (reasoning field dropped; cost logged as 0 and GPU time tracked separately)."""
    url = URL
    if body.get("model", "").startswith("modal/"):
        body = dict(body)
        body["model"] = body["model"].split("/", 1)[1]
        body.pop("reasoning", None)
        url = env("MODAL_VLLM_URL").rstrip("/") + "/v1/chat/completions"
    data = json.dumps(body).encode()
    hdr = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    for attempt in range(tries):
        try:
            t0 = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdr), timeout=300) as r:
                return json.load(r), time.time() - t0
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code == 402:
                raise RuntimeError("OpenRouter credit exhausted: " + msg)
            if e.code in (408, 429, 500, 502, 503, 524) and attempt < tries - 1:
                time.sleep(2 ** attempt + random.random())
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def gold_ids(item, pool_name):
    g = {f"en:gold:{item['id']}", f"{item['lang']}:gold:{item['id']}"}
    if item.get("gold_L_chunk_id"):
        g.add(item["gold_L_chunk_id"])
    for cid in item.get("gold_en_chunk_ids", []):
        g.add(cid)
    return g


def is_gold_hit(hit, item):
    """A hit counts as gold if it is an injected gold chunk, the located L gold chunk, or any chunk of the
    item's English/L article that contains a gold answer string."""
    if hit["id"] in gold_ids(item, None):
        return True
    t = hit["title"]
    if t and (t == item.get("en_title") or t == item.get("L_title")):
        txt = norm(hit["text"])
        return any(norm(a) in txt for a in (item.get("ans_en") or []) + (item.get("ans_L") or []) if norm(a))
    return False


def norm(s):
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[।॥.,;:!?\"'()\[\]{}«»“”‘’\-–—/]", " ", s)
    return " ".join(s.split())


def format_hits(hits):
    if not hits:
        return NO_RESULTS
    out = []
    for i, h in enumerate(hits, 1):
        out.append(f"[{i}] ({h['lang']}) {h['text'][:1200]}")
    return "\n\n".join(out)


def run_episode(model, item, qlang, policy, pool_name, searcher, key, reasoning="minimal", stage="main"):
    question = item["q_en"] if qlang == "en" else item["q_L"]
    qlang_name = LANG_NAME[qlang]
    sys_prompt = SYSTEM_AGENT.format(max_searches=MAX_SEARCHES, k=K,
                                     policy=POLICY[policy].format(qlang=qlang_name))
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}]
    searches, calls, cost, tin, tout, lat = [], 0, 0.0, 0, 0, 0.0
    n_steps = 0
    final = None
    finish = None
    while True:
        allow_tools = n_steps < MAX_SEARCHES
        body = {"model": model, "temperature": 0, "messages": messages,
                "max_tokens": MAX_TOKENS_STEP if allow_tools else MAX_TOKENS_FINAL,
                "reasoning": {"effort": reasoning}}
        if allow_tools:
            body["tools"] = [TOOL_SEARCH]
            body["tool_choice"] = "auto"
        for attempt in range(3):
            resp, l = post(body, key)
            calls += 1
            lat += l
            u = resp.get("usage", {})
            c = float(u.get("cost", 0.0))
            cost += c
            tin += int(u.get("prompt_tokens") or 0)
            tout += int(u.get("completion_tokens") or 0)
            cost_tracker.log_call(model, c, stage)
            choice = (resp.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            finish = choice.get("finish_reason")
            if finish == "error" or (not choice) or (resp.get("error") and not msg):
                # provider-side error returned with HTTP 200 (finish_reason "error"); retry, do not store
                time.sleep(3 + 5 * attempt)
                continue
            break
        else:
            raise RuntimeError("provider error on 3 attempts: " + str(resp.get("error") or choice)[:200])
        tcs = msg.get("tool_calls") or []
        if tcs and allow_tools:
            # one step may contain several tool calls (dual policy issues two)
            messages.append({"role": "assistant", "content": msg.get("content") or None, "tool_calls": tcs})
            for tc in tcs:
                try:
                    q = json.loads(tc["function"]["arguments"]).get("query", "")
                except Exception:
                    q = tc["function"]["arguments"]
                hits = searcher.search(q, K) if searcher else []
                searches.append({"step": n_steps + 1, "query": q, "script": script_of(q),
                                 "hit_ids": [h["id"] for h in hits], "hit_langs": [h["lang"] for h in hits],
                                 "gold_hit": any(is_gold_hit(h, item) for h in hits)})
                messages.append({"role": "tool", "tool_call_id": tc["id"], "name": "search", "content": format_hits(hits)})
            n_steps += 1
            continue
        final = (msg.get("content") or "").strip()
        if not final and finish == "length":
            final = ""
        break
    return {"model": model, "item": item["id"], "lang": item["lang"], "source": item["source"], "qlang": qlang,
            "policy": policy, "pool": pool_name, "question": question, "answer": final, "finish": finish,
            "searches": searches, "n_searches": len(searches), "n_steps": n_steps, "calls": calls,
            "tin": tin, "tout": tout, "cost": round(cost, 7), "latency": round(lat, 2),
            "t": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run_closed(model, item, qlang, key, reasoning="minimal", stage="closed"):
    question = item["q_en"] if qlang == "en" else item["q_L"]
    body = {"model": model, "temperature": 0, "max_tokens": MAX_TOKENS_FINAL, "reasoning": {"effort": reasoning},
            "messages": [{"role": "system", "content": SYSTEM_CLOSED}, {"role": "user", "content": question}]}
    resp, l = post(body, key)
    u = resp.get("usage", {})
    c = float(u.get("cost", 0.0))
    cost_tracker.log_call(model, c, stage)
    return {"model": model, "item": item["id"], "lang": item["lang"], "source": item["source"], "qlang": qlang,
            "policy": "closed", "pool": "none", "question": question,
            "answer": (resp["choices"][0]["message"].get("content") or "").strip(),
            "finish": resp["choices"][0].get("finish_reason"), "searches": [], "n_searches": 0, "n_steps": 0,
            "calls": 1, "tin": u.get("prompt_tokens"), "tout": u.get("completion_tokens"), "cost": round(c, 7),
            "latency": round(l, 2), "t": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run_oracle(model, item, qlang, passage_lang, key, reasoning="minimal", stage="oracle"):
    question = item["q_en"] if qlang == "en" else item["q_L"]
    passage = item["gold_en"] if passage_lang == "en" else item.get("gold_L")
    body = {"model": model, "temperature": 0, "max_tokens": MAX_TOKENS_FINAL, "reasoning": {"effort": reasoning},
            "messages": [{"role": "system", "content": SYSTEM_ORACLE},
                         {"role": "user", "content": USER_ORACLE.format(passage=passage, question=question)}]}
    resp, l = post(body, key)
    u = resp.get("usage", {})
    c = float(u.get("cost", 0.0))
    cost_tracker.log_call(model, c, stage)
    return {"model": model, "item": item["id"], "lang": item["lang"], "source": item["source"], "qlang": qlang,
            "policy": f"oracle_{passage_lang}", "pool": "oracle", "question": question,
            "answer": (resp["choices"][0]["message"].get("content") or "").strip(),
            "finish": resp["choices"][0].get("finish_reason"), "searches": [], "n_searches": 0, "n_steps": 0,
            "calls": 1, "tin": u.get("prompt_tokens"), "tout": u.get("completion_tokens"), "cost": round(c, 7),
            "latency": round(l, 2), "t": time.strftime("%Y-%m-%dT%H:%M:%S")}
