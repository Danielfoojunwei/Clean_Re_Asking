"""Model labels and groups used by the G, H and I analyses."""
LABEL = {
    "x-ai/grok-4.3": "Grok 4.3", "openai/gpt-4.1-mini": "GPT-4.1-mini", "google/gemini-2.5-flash": "Gemini 2.5 Flash", "anthropic/claude-haiku-5.5": "Claude Haiku 5.5",
    "deepseek/deepseek-v3.2": "DeepSeek v3.2", "meta-llama/llama-4-maverick": "Llama 4 Maverick", "qwen/qwen3.5-9b": "Qwen3.5-9B", "amazon/nova-lite-v1": "Nova Lite",
    "openai/gpt-6-luna-pro": "GPT-6 Luna Pro", "openai/gpt-6-luna": "GPT-6 Luna", "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
    "mistralai/ministral-14b-2512": "Ministral 14B", "mistralai/ministral-8b-2512": "Ministral 8B", "mistralai/ministral-3b-2512": "Ministral 3B",
    "z-ai/glm-5.2": "GLM-5.2", "deepseek/deepseek-v4-flash": "DeepSeek-V4-Flash", "qwen/qwen3.5-397b-a17b": "Qwen3.5-397B", "minimax/minimax-m3": "MiniMax-M3",
    "google/gemini-3-flash-preview": "Gemini 3 Flash", "anthropic/claude-sonnet-5": "Claude Sonnet 5", "openai/gpt-5.6-luna": "GPT-5.6 Luna"}
FIRST8 = list(LABEL)[:8]
BASTA = ["deepseek/deepseek-v3.2"] + list(LABEL)[8:14]   # the seven models of Basta et al. 2026
YANG = ["x-ai/grok-4.3"] + list(LABEL)[14:]              # eight of Yang et al. 2026 (Grok 4.3 shared)
# Published concession rates when the user is wrong (F) and right (H), Basta et al. 2026, Figure 2 (escalating arm)
BASTA_PUB = {"GPT-6 Luna Pro": {"authority": (.05, .55), "citation": (.14, .70), "plain": (.03, .39), "persistence": (.21, .83), "neutral": (.01, .05)},
             "GPT-6 Luna": {"authority": (.07, .61), "citation": (.14, .67), "plain": (.04, .46), "persistence": (.25, .83), "neutral": (.00, .03)},
             "DeepSeek v3.2": {"authority": (.82, .92), "citation": (.97, .93), "plain": (.55, .79), "persistence": (.93, .96), "neutral": (.00, .12)},
             "Llama 3.3 70B": {"authority": (.97, .99), "citation": (.96, .98), "plain": (.99, .99), "persistence": (1.00, .99), "neutral": (.04, .15)},
             "Ministral 14B": {"authority": (.75, .90), "citation": (.78, .86), "plain": (.53, .83), "persistence": (.69, .92), "neutral": (.11, .39)},
             "Ministral 8B": {"authority": (.66, .88), "citation": (.81, .91), "plain": (.56, .84), "persistence": (.69, .91), "neutral": (.04, .33)},
             "Ministral 3B": {"authority": (.62, .88), "citation": (.74, .86), "plain": (.74, .90), "persistence": (.79, .89), "neutral": (.21, .40)}}
