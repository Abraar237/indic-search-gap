#!/bin/bash
# Reduced remainder of the OpenRouter grid (shared key at $24 on 2026-10-10 20:40): essentials only.
cd "$(dirname "$0")/.."
export TOKENIZERS_PARALLELISM=false
R="python3 experiments/indic_runner.py"
FL25=google/gemini-2.5-flash-lite
FL31=google/gemini-3.1-flash-lite
F36=google/gemini-3.6-flash
CORE15="L:free:en,L:free:L,L:free:both,L:match:en,L:match:L,L:match:both,L:english:en,L:english:L,L:english:both,L:dual:en,L:dual:L,L:dual:both,en:free:en,en:free:L,en:free:both"
HEAD="L:free:en,L:free:both,L:dual:en,L:dual:both,en:free:en,en:free:both,L:english:en,L:english:both"

set -x
$R --model $FL25 --grid native_te --langs te                        >> results/logs/fl25_native.log     2>&1
$R --model $FL31 --grid core   --langs hi,te --items 100 --cells "$CORE15" >> results/logs/fl31_core_dense.log 2>&1
$R --model $FL31 --grid closed --langs hi,te --items 100           >> results/logs/fl31_closed.log     2>&1
$R --model $FL31 --grid oracle --langs hi,te --items 100           >> results/logs/fl31_oracle.log     2>&1
$R --model $F36  --grid core   --langs hi,te --items 50 --cells "$HEAD" >> results/logs/f36_head_dense.log 2>&1
$R --model $F36  --grid closed --langs hi,te --items 50            >> results/logs/f36_closed.log      2>&1
$R --model $F36  --grid oracle --langs hi,te --items 50            >> results/logs/f36_oracle.log      2>&1
echo ALL_OPENROUTER_DONE
