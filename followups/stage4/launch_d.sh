#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
python3 run_d.py --model deepseek/deepseek-v3.2 --rounds 1-4 --cap 0.9 > logd_deepseek.txt 2>&1 &
python3 run_d.py --model meta-llama/llama-4-maverick --rounds 1-4 --cap 1.0 > logd_llama.txt 2>&1 &
python3 run_d.py --model qwen/qwen3.5-9b --rounds 1-4 --cap 0.5 --workers 5 > logd_qwen.txt 2>&1 &
python3 run_d.py --model amazon/nova-lite-v1 --rounds 1-4 --cap 0.25 > logd_nova.txt 2>&1 &
python3 run_d.py --model google/gemini-2.5-flash --rounds 1-4 --cap 1.0 > logd_gemini.txt 2>&1 &
python3 run_d.py --model openai/gpt-4.1-mini --rounds 1-4 --cap 1.2 > logd_mini.txt 2>&1 &
python3 run_d.py --model anthropic/claude-haiku-5.5 --rounds 1-4 --cap 0.3 > logd_haiku.txt 2>&1 &
python3 run_d.py --model x-ai/grok-4.3 --rounds 1-2 --cap 1.4 > logd_grok.txt 2>&1 &
wait
