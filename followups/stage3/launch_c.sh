#!/bin/bash
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
seq5() {  # model, cap, workers
  for spec in "X1 1-9" "X7 1-9" "X2 1-5" "X3 1-5" "X4 1-5"; do set -- "$1" "$2" "$3" $spec; python3 run_c.py --model "$1" --exp "$4" --rounds "$5" --cap "$2" --workers "$3"; done
}
(seq5 deepseek/deepseek-v3.2 0.75 8; python3 run_c.py --model deepseek/deepseek-v3.2 --exp X6 --rounds 1-4 --cap 0.95) > logc_deepseek.txt 2>&1 &
(seq5 meta-llama/llama-4-maverick 0.95 8) > logc_llama.txt 2>&1 &
(seq5 qwen/qwen3.5-9b 0.45 4; python3 run_c.py --model qwen/qwen3.5-9b --exp X6 --rounds 1-4 --cap 0.6 --workers 4) > logc_qwen.txt 2>&1 &
(seq5 amazon/nova-lite-v1 0.25 8) > logc_nova.txt 2>&1 &
(seq5 google/gemini-2.5-flash 0.9 8; python3 run_c.py --model google/gemini-2.5-flash --exp X6 --rounds 1-4 --cap 1.5) > logc_gemini.txt 2>&1 &
(python3 run_c.py --model x-ai/grok-4.3 --exp X1 --rounds 1-4 --cap 0.45; python3 run_c.py --model x-ai/grok-4.3 --exp X7 --rounds 1-4 --cap 0.75; python3 run_c.py --model x-ai/grok-4.3 --exp X2 --rounds 1-3 --cap 1.1) > logc_grok.txt 2>&1 &
python3 run_c.py --model anthropic/claude-haiku-5.5 --exp X6 --rounds 1-4 --cap 0.3 > logc_haiku.txt 2>&1 &
python3 run_c.py --model openai/gpt-4.1 --exp X5 --rounds 6-11 --cap 1.0 > logc_gpt41.txt 2>&1 &
wait
