#!/bin/bash
# Resume only what was cut off by the key limit: G gaps, H gaps, all of I, J-logprob gaps. (J-sample is left as it stands.)
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY before running}"
W=3
(python3 run_g.py --model openai/gpt-6-luna-pro --cap 6 --workers $W; python3 run_g.py --model openai/gpt-6-luna-pro --cap 6 --workers $W --extra; python3 run_h.py --model openai/gpt-6-luna-pro --cap 4 --workers $W) > logf_lunapro.txt 2>&1 &
(python3 run_g.py --model deepseek/deepseek-v3.2 --cap 6 --workers $W --blocks 4-7; python3 run_g.py --model deepseek/deepseek-v3.2 --cap 6 --workers $W --blocks 4-7 --extra; python3 run_h.py --model deepseek/deepseek-v3.2 --cap 4 --workers $W; python3 run_j.py --model deepseek/deepseek-v3.2 --mode logprob --blocks 0-3 --cap 1 --workers 2) > logf_deepseek.txt 2>&1 &
(python3 run_g.py --model qwen/qwen3.5-397b-a17b --cap 6 --workers $W; python3 run_j.py --model qwen/qwen3.5-397b-a17b --mode logprob --blocks 0-3 --cap 1 --workers 2) > logf_qwen397.txt 2>&1 &
python3 run_g.py --model anthropic/claude-sonnet-5 --cap 6 --workers $W > logf_sonnet.txt 2>&1 &
python3 run_g.py --model z-ai/glm-5.2 --cap 6 --workers $W > logf_glm.txt 2>&1 &
python3 run_h.py --model x-ai/grok-4.3 --cap 4 --workers $W > logf_grok.txt 2>&1 &
wait
bash launch_i.sh
