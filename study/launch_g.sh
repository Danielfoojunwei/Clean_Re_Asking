#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
python3 run_g.py --model deepseek/deepseek-v3.2 --cap 1.0 > logg_deepseek.txt 2>&1 &
python3 run_g.py --model meta-llama/llama-4-maverick --cap 1.0 > logg_llama.txt 2>&1 &
python3 run_g.py --model qwen/qwen3.5-9b --cap 0.6 --workers 6 > logg_qwen.txt 2>&1 &
python3 run_g.py --model amazon/nova-lite-v1 --cap 0.3 > logg_nova.txt 2>&1 &
python3 run_g.py --model google/gemini-2.5-flash --cap 1.2 > logg_gemini.txt 2>&1 &
python3 run_g.py --model openai/gpt-4.1-mini --cap 1.2 > logg_mini.txt 2>&1 &
python3 run_g.py --model anthropic/claude-haiku-5.5 --cap 1.2 --long > logg_haiku.txt 2>&1 &
python3 run_g.py --model x-ai/grok-4.3 --cap 2.0 > logg_grok.txt 2>&1 &
wait
