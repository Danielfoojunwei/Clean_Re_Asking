#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
ALL="x-ai/grok-4.3 openai/gpt-4.1-mini google/gemini-2.5-flash deepseek/deepseek-v3.2 meta-llama/llama-4-maverick qwen/qwen3.5-9b amazon/nova-lite-v1 openai/gpt-6-luna-pro openai/gpt-6-luna meta-llama/llama-3.3-70b-instruct mistralai/ministral-14b-2512 mistralai/ministral-8b-2512 mistralai/ministral-3b-2512 z-ai/glm-5.2 deepseek/deepseek-v4-flash qwen/qwen3.5-397b-a17b minimax/minimax-m3 google/gemini-3-flash-preview anthropic/claude-sonnet-5 openai/gpt-5.6-luna"
for m in $ALL; do python3 run_h.py --exp q --out runs_q --model $m --cap 1.5 --workers 2 > logq_$(basename $m).txt 2>&1 & done
python3 run_h.py --exp q --out runs_q --model anthropic/claude-haiku-5.5 --cap 1.5 --workers 2 --long > logq_haiku.txt 2>&1 &
wait
