#!/bin/bash
# Open-weight arm (Qwen3-30B-A3B on Modal vLLM): full core dense + bm25 headline + closed + oracle. Parallel to run_all.sh.
cd "$(dirname "$0")/.."
export TOKENIZERS_PARALLELISM=false
mkdir -p results/logs
R="python3 experiments/indic_runner.py"
Q=modal/Qwen3-30B-A3B-Instruct-2507
HEAD="L:free:en,L:free:both,L:dual:en,L:dual:both,en:free:en,en:free:both,L:match:en,L:match:both"
set -x
$R --model $Q --grid core   --langs hi,te                          >> results/logs/qwen_core_dense.log 2>&1
$R --model $Q --grid core   --langs hi,te --retriever bm25 --cells "$HEAD" >> results/logs/qwen_head_bm25.log 2>&1
$R --model $Q --grid closed --langs hi,te                          >> results/logs/qwen_closed.log 2>&1
$R --model $Q --grid oracle --langs hi,te                          >> results/logs/qwen_oracle.log 2>&1
$R --model $Q --grid native_te --langs te                          >> results/logs/qwen_native.log 2>&1
echo ALL_MODAL_DONE
