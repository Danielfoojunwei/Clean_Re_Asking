#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
python3 run_e.py --model deepseek/deepseek-v3.2 --rounds 1-2 --cap 0.35 > loge_deepseek.txt 2>&1 &
python3 run_e.py --model meta-llama/llama-4-maverick --rounds 1-2 --cap 0.3 > loge_llama.txt 2>&1 &
python3 run_e.py --model qwen/qwen3.5-9b --rounds 1-2 --cap 0.2 --workers 5 > loge_qwen.txt 2>&1 &
python3 run_e.py --model amazon/nova-lite-v1 --rounds 1-2 --cap 0.1 > loge_nova.txt 2>&1 &
python3 run_e.py --model google/gemini-2.5-flash --rounds 1-2 --cap 0.3 > loge_gemini.txt 2>&1 &
python3 run_e.py --model openai/gpt-4.1-mini --rounds 1-2 --cap 0.4 > loge_mini.txt 2>&1 &
python3 run_e.py --model anthropic/claude-haiku-5.5 --rounds 1-2 --cap 0.35 --long > loge_haiku.txt 2>&1 &
python3 run_e.py --model x-ai/grok-4.3 --rounds 1-2 --cap 0.5 > loge_grok.txt 2>&1 &
wait
