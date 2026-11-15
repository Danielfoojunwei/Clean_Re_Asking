#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
W=4
NEW="openai/gpt-6-luna-pro openai/gpt-6-luna meta-llama/llama-3.3-70b-instruct mistralai/ministral-14b-2512 mistralai/ministral-8b-2512 mistralai/ministral-3b-2512 z-ai/glm-5.2 deepseek/deepseek-v4-flash qwen/qwen3.5-397b-a17b minimax/minimax-m3 google/gemini-3-flash-preview anthropic/claude-sonnet-5 openai/gpt-5.6-luna"
OLD="deepseek/deepseek-v3.2 meta-llama/llama-4-maverick qwen/qwen3.5-9b amazon/nova-lite-v1 google/gemini-2.5-flash openai/gpt-4.1-mini x-ai/grok-4.3"
BASTA="openai/gpt-6-luna-pro openai/gpt-6-luna meta-llama/llama-3.3-70b-instruct mistralai/ministral-14b-2512 mistralai/ministral-8b-2512 mistralai/ministral-3b-2512"
n() { basename "$1"; }
# H-a: thirteen more models on the G protocol (core, then Amendment G-1 conditions)
for m in $NEW; do (python3 run_g.py --model $m --cap 6 --workers $W > logha_$(n $m).txt 2>&1; python3 run_g.py --model $m --cap 6 --workers $W --extra >> logha_$(n $m).txt 2>&1) & done
# H-b: blocks 4-7 for the first eight models (and the G-1 conditions on all eight blocks)
for m in $OLD; do (python3 run_g.py --model $m --cap 6 --workers $W --extra > loghb_$(n $m).txt 2>&1; python3 run_g.py --model $m --cap 6 --workers $W --blocks 4-7 >> loghb_$(n $m).txt 2>&1; python3 run_g.py --model $m --cap 6 --workers $W --blocks 4-7 --extra >> loghb_$(n $m).txt 2>&1) & done
(python3 run_g.py --model anthropic/claude-haiku-5.5 --cap 6 --workers $W --long --blocks 4-7 > loghb_haiku.txt 2>&1; python3 run_g.py --model anthropic/claude-haiku-5.5 --cap 6 --workers $W --long --blocks 4-7 --extra >> loghb_haiku.txt 2>&1) &
# H-c, H-d, H-e: fourteen models
for m in $OLD $BASTA; do python3 run_h.py --model $m --cap 4 --workers $W > loghc_$(n $m).txt 2>&1 & done
python3 run_h.py --model anthropic/claude-haiku-5.5 --cap 4 --workers $W --long > loghc_haiku.txt 2>&1 &
wait
