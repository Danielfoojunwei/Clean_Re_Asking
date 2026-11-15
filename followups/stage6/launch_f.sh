#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
python3 run_f.py --model deepseek/deepseek-v3.2 --cap 0.4 > logf_deepseek.txt 2>&1 &
python3 run_f.py --model meta-llama/llama-4-maverick --cap 0.35 > logf_llama.txt 2>&1 &
python3 run_f.py --model qwen/qwen3.5-9b --cap 0.25 --workers 5 > logf_qwen.txt 2>&1 &
python3 run_f.py --model amazon/nova-lite-v1 --cap 0.1 > logf_nova.txt 2>&1 &
python3 run_f.py --model google/gemini-2.5-flash --cap 0.35 > logf_gemini.txt 2>&1 &
python3 run_f.py --model openai/gpt-4.1-mini --cap 0.45 > logf_mini.txt 2>&1 &
python3 run_f.py --model anthropic/claude-haiku-5.5 --cap 0.4 --long > logf_haiku.txt 2>&1 &
python3 run_f.py --model x-ai/grok-4.3 --cap 0.6 > logf_grok.txt 2>&1 &
wait
