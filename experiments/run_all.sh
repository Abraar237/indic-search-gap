#!/bin/bash
# Full grid, sequential per key (OpenRouter), logs in results/logs/. Resume-safe: rerun to continue.
cd "$(dirname "$0")/.."
export TOKENIZERS_PARALLELISM=false
mkdir -p results/logs
R="python3 experiments/indic_runner.py"
FL25=google/gemini-2.5-flash-lite
FL31=google/gemini-3.1-flash-lite
F36=google/gemini-3.6-flash
HEAD="L:free:en,L:free:both,L:dual:en,L:dual:both,en:free:en,en:free:both,L:match:en,L:match:both"
set -x
# 0. flash-lite 2.5: finish closed + oracle (resume), then
$R --model $FL25 --grid closed --langs hi,te >> results/logs/fl25_closed.log 2>&1
$R --model $FL25 --grid oracle --langs hi,te >> results/logs/fl25_oracle.log 2>&1
# 1. flash-lite 2.5: full core, dense (main) then bm25 (retriever factor), batteries
$R --model $FL25 --grid core   --langs hi,te                       >> results/logs/fl25_core_dense.log 2>&1
$R --model $FL25 --grid core   --langs hi,te --retriever bm25      >> results/logs/fl25_core_bm25.log  2>&1
$R --model $FL25 --grid noise  --langs hi,te                       >> results/logs/fl25_noise.log      2>&1
$R --model $FL25 --grid none   --langs hi,te                       >> results/logs/fl25_none.log       2>&1
$R --model $FL25 --grid native_te --langs te                       >> results/logs/fl25_native.log     2>&1
# 2. flash-lite 3.1: core dense on 120 items/language; bm25 on headline cells; closed + oracle
$R --model $FL31 --grid core   --langs hi,te --items 120           >> results/logs/fl31_core_dense.log 2>&1
$R --model $FL31 --grid core   --langs hi,te --items 120 --retriever bm25 --cells "$HEAD" >> results/logs/fl31_head_bm25.log 2>&1
$R --model $FL31 --grid closed --langs hi,te --items 120           >> results/logs/fl31_closed.log     2>&1
$R --model $FL31 --grid oracle --langs hi,te --items 120           >> results/logs/fl31_oracle.log     2>&1
# 3. gemini-3.6-flash: headline cells dense on 60 items/language; closed + oracle on the same items
$R --model $F36  --grid core   --langs hi,te --items 60 --cells "$HEAD" >> results/logs/f36_head_dense.log 2>&1
$R --model $F36  --grid closed --langs hi,te --items 60            >> results/logs/f36_closed.log      2>&1
$R --model $F36  --grid oracle --langs hi,te --items 60            >> results/logs/f36_oracle.log      2>&1
echo ALL_OPENROUTER_DONE
