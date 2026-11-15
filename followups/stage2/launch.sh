#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
AB=exact,nochain,norev,placebo,balanced
(python3 run_b.py --model deepseek/deepseek-v3.2 --rounds 1-9 --conds base,explicit,$AB --cap 0.55 && python3 run_b.py --model deepseek/deepseek-v3.2 --rounds 1-9 --conds balanced --exps E5 --cap 0.9) > log_deepseek.txt 2>&1 &
(python3 run_b.py --model meta-llama/llama-4-maverick --rounds 1-9 --conds base,explicit,$AB --cap 0.75 && python3 run_b.py --model meta-llama/llama-4-maverick --rounds 1-9 --conds balanced --exps E5 --cap 1.1) > log_llama.txt 2>&1 &
(python3 run_b.py --model qwen/qwen3.5-9b --rounds 1-9 --conds base,explicit,$AB --cap 0.4 --workers 4 && python3 run_b.py --model qwen/qwen3.5-9b --rounds 1-9 --conds balanced --exps E5 --cap 0.6 --workers 4) > log_qwen.txt 2>&1 &
(python3 run_b.py --model amazon/nova-lite-v1 --rounds 1-9 --conds $AB --cap 0.2 && python3 run_b.py --model amazon/nova-lite-v1 --rounds 1-9 --conds balanced --exps E5 --cap 0.3) > log_nova.txt 2>&1 &
(python3 run_b.py --model google/gemini-2.5-flash --rounds 1-9 --conds $AB --cap 0.7 && python3 run_b.py --model google/gemini-2.5-flash --rounds 1-9 --conds balanced --exps E5 --cap 1.2) > log_gemini.txt 2>&1 &
python3 run_b.py --model x-ai/grok-4.3 --rounds 1-4 --conds $AB --cap 1.0 > log_grok.txt 2>&1 &
wait
