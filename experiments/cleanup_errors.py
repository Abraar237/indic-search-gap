#!/usr/bin/env python3
"""Drop records whose final turn ended in a provider error (finish_reason == 'error') so a resume re-runs them.
Run only when no runner is writing to the file. Keeps a copy of the dropped lines in results/raw/_discarded_errors.jsonl."""
import glob, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
for f in glob.glob(str(ROOT / "results" / "raw" / "*.jsonl")):
    if "_discarded" in f: continue
    keep, drop = [], []
    for line in open(f):
        r = json.loads(line)
        (drop if r.get("finish") == "error" else keep).append(line)
    if drop:
        open(ROOT / "results" / "raw" / "_discarded_errors.jsonl", "a").writelines(drop)
        open(f, "w").writelines(keep)
    print(pathlib.Path(f).name, "kept", len(keep), "dropped", len(drop))
