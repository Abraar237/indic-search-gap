"""Spend tracker with hard stop. Every OpenRouter call logs the exact `usage.cost` it returned.
State: results/spend.json. Raises CostCapExceeded once the total crosses HARD_STOP_USD.
The OpenRouter key is shared with ../cache layout cost research/ (its own tracker, also $24)."""

import fcntl
import json
import os
import threading
import time

HARD_STOP_USD = 24.00
STATE = os.path.join(os.path.dirname(__file__), "..", "results", "spend.json")
_lock = threading.Lock()


class CostCapExceeded(RuntimeError):
    pass


def _load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"total_usd": 0.0, "by_model": {}, "by_stage": {}, "n_calls": 0, "updated": None}


def log_call(model, cost_usd, stage="main"):
    """Thread- and process-safe: an flock on a sidecar lock file guards read-modify-write, and the state is
    written to a temp file then atomically replaced (two concurrent runners corrupted the plain write once)."""
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with _lock, open(STATE + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            s = _load()
            s["total_usd"] = round(s["total_usd"] + float(cost_usd), 6)
            s["by_model"][model] = round(s["by_model"].get(model, 0.0) + float(cost_usd), 6)
            s["by_stage"][stage] = round(s["by_stage"].get(stage, 0.0) + float(cost_usd), 6)
            s["n_calls"] += 1
            s["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            tmp = STATE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(s, f, indent=1)
            os.replace(tmp, STATE)
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)
        if s["total_usd"] >= HARD_STOP_USD:
            raise CostCapExceeded(f"spend {s['total_usd']:.2f} >= {HARD_STOP_USD}")
        return s["total_usd"]


def total():
    return _load()["total_usd"]


def remaining_credit():
    """Live remaining credit on the shared OpenRouter key (None on error). Never prints the key."""
    import urllib.request
    try:
        root = os.path.join(os.path.dirname(__file__), "..")
        key = [l.split("=", 1)[1].strip() for l in open(os.path.join(root, ".env")) if l.startswith("OPENROUTER_API_KEY=")][0]
        req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=30) as r:
            return float(json.load(r)["data"].get("limit_remaining") or 0)
    except Exception:
        return None
