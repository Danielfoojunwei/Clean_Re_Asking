# Follow-up plan (written before any follow-up result)

Written 2026-11-14T22:32:36Z. The main study (PLAN.md in benchmark_v2) is frozen and unchanged. Twenty-eight test calls were made
to check which providers return token probabilities; their answers are not used.

## Why
The main study only read model outputs. Three things it could not say:
1. Stated confidence was flat (97% said 100). Is there a usable uncertainty signal the model does not report?
2. The extra sentence did two jobs (no reversing, no chaining) and raised refusals of allowed requests. Which part does that,
   is it just "any extra sentence", and can a sentence stop chaining without raising refusals?
3. Models found the rule when asked directly yet refused the request. Is "the rule is listed" present inside the model at the
   moment it decides, and does changing it change the decision?

## Part A: token probabilities (hosted)
Models: DeepSeek v3.2, Llama 4 Maverick, Qwen3.5-9B (the three of nine whose providers return token probabilities; the provider is
pinned to one that does, so it can differ from the main study and is logged). Quick-answer items, rounds 1-9, frozen prompts, both wordings.
Signal: probability of the chosen word minus the other word, from the first answer token's top-5 list (a word missing from the
top 5 gets the smallest listed probability).
- A1 (met if): AUROC for telling right from wrong answers is at least 0.65 with a 95% bootstrap interval over name sets above 0.5.
- A2: report the same AUROC separately for wrong allows and wrong refusals.

## Part B: which sentence does what (hosted)
Quick answers, rounds 1-9 (Grok 4.3 rounds 1-4 for cost), models: DeepSeek v3.2, Llama 4 Maverick, Qwen3.5-9B, Nova Lite, Gemini 2.5 Flash, Grok 4.3.
Conditions added to the frozen "as first written" and "extra sentence" prompts: exact-line only; no-chaining only; no-reversing only;
a neutral filler sentence; and a balanced sentence (the extra sentence plus "if the exact line is listed, it is allowed").
Step-by-step answers are run for the balanced sentence on the five lower-cost models.
A change counts if it is at least 5 points with a 95% interval over name sets that excludes zero.
- B1: the filler sentence does not raise refusals of allowed requests (if it does, the effect is "any extra sentence").
- B2: report which single part (exact, no-chaining, no-reversing) raises refusals of allowed requests.
- B3: the balanced sentence keeps wrongly allowed chain requests within 3 points of the extra sentence and brings refusals of
  allowed requests back to no more than the as-first-written rate.

## Part C: inside an open model (local)
Model: Qwen2.5-1.5B-Instruct, chosen because it is the largest instruction model that runs on the available CPU-only machine. It is not
one of the nine hosted models. Quick-answer and rule-lookup prompts, rounds 0-11 (24 name sets), decision read from the next-token scores of the two answer words.
- C0 (gate): the model is above 60% correct overall and shows at least one of the two failures (chain requests allowed, allowed requests refused) at 10% or more. If not, Part C is reported as not informative.
- C1: a linear probe on the last-token activations predicts "the exact rule is listed" on held-out name sets better than the model's own decision does. Control: same probe with shuffled labels; layer sweep.
- C2: a linear probe predicts whether the model's answer is correct; compared with the model's own answer-probability gap.
- C3 (causal): adding the C1 direction to the activations flips wrong refusals to allows more than a random direction of the same size, on held-out name sets.

## Spend
Hard cap USD 5.10 across hosted calls (per-model caps in the run commands).

sha256 gen_b.py: e07dfb2fae73d0ad2c4a80cefafea0455d534d716816099bede60d966e9ba8e5
sha256 run_b.py: 923cd7d532fd78d6b59cf6b4e00926ddbeebc4bdd6d1627f1a061db14e506c0e

## Amendment B-1 (2026-11-14T22:38:07Z)
DeepSeek v3.2: 5,666 of 6,081 token-probability calls failed with provider error 400 (the providers that advertise token probabilities
rejected the request). The 415 that succeeded are kept. Change: DeepSeek's Part B conditions are run without token probabilities on
default routing; its two frozen conditions are retried for token probabilities pinned to the one provider that answered (DigitalOcean).
Runner gained two flags (--only, --no-logprobs); prompts and scoring are unchanged. No DeepSeek Part B result had been looked at
beyond a partial table produced while the run was failing.
sha256 run_b.py (amended): 80541e296ea298e9a54e5889036081c2284d0a5039757557549850ab6cdbed06

## Amendment B-2 (2026-11-15T01:18:11Z): Part C stopped at its gate
Qwen2.5-1.5B-Instruct was 50.3% correct on the first 960 quick-answer items (three name-set rounds; interval over name sets 49-52%),
below the 60% gate C0. It allowed 64% of unconnected requests, so it is not doing the task. A second candidate, Qwen2.5-3B-Instruct, was
tried on 96 items and was 55% correct. Per C0, Part C is reported as not informative: no probe or steering result is claimed. A probe
on a model that performs at chance cannot speak to the failures of models that perform well above it. The two earlier extraction runs
were lost to the machine's two-hour job limit before this point and produced no data. Probing one of the nine study models needs a GPU,
which this machine does not have.
