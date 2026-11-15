# Stage 3 plan: why each failure happens (written before any Stage 3 result)

Written 2026-11-15T00:35:29Z.

## How the stages fit together
The study asks one question in three steps, and each step was fixed in writing before its data existed.
- Stage 1 (PLAN.md, 14 Nov 14:48-15:41 UTC): WHAT goes wrong. Result: three failures behind one score: chaining, refusing allowed
  requests, and no usable self-report.
- Stage 2 (PLAN_B.md, 14 Nov): IS THE SIGNAL THERE, AND WHICH WORDS MATTER. Result so far: token probabilities separate right from wrong
  (AUROC 0.78-0.87) where stated confidence did not; every restrictive part of the extra sentence raises refusals; a "balanced"
  sentence does not undo it for most models. Part C (inside an open model) is still running.
- Stage 3 (this file): WHY, and HOW FAR IT GOES. One experiment per open question left by Stages 1-2, each tied to one of the three
  failures. Nothing below has been run except 60 smoke-test calls on a name set (round 0) that no Stage 3 analysis uses.

Stages 2 and 3 were designed after seeing Stage 1, and Stage 3 after seeing Stage 2's hosted results. They are follow-ups, not part of
the original registration, and are reported as such.

## Rules shared by all experiments
Unit: name set (round x naming style). Intervals: 95% bootstrap over name sets. A change "counts" if it is at least 10 points and its
interval excludes zero. Malformed answers count as wrong. Temperature 0. Hidden reasoning off except X6. Prompts not listed as changed
are the frozen Stage 1 prompts, byte for byte. Models: the five lower-cost models that showed the failures (DeepSeek v3.2, Llama 4
Maverick, Qwen3.5-9B, Nova Lite, Gemini 2.5 Flash), plus Grok 4.3 (the heaviest refuser) on fewer rounds where noted.

## Failure 1: chaining
- X4 Is it the word "route"? Frozen prompts with "route" replaced by "entry" (quick and step-by-step, as-first-written wording, rounds 1-5).
  Prediction: step-by-step chaining falls by a counting amount in at least 3 of 5 models. If it does, chaining is a reading of one word.
  If it does not, the Stage 1 claim narrows to: models chain unless chaining is forbidden.

## Failure 2: refusing allowed requests
- X1 Does it grow with the rulebook? The same focal rules and requests, padded with unrelated rules to 8, 16 and 32 lines, order shuffled
  (quick answers, as first written, rounds 1-9; Grok rounds 1-4). Size 4 is the Stage 1 data.
  Predictions: (a) refusals of allowed requests rise by a counting amount from 4 to 32 rules in at least 3 of 6 models; (b) within the
  16- and 32-rule books, refusals are higher when the matching rule is in the last third than in the first third (confirming the Stage 1
  exploratory position effect); (c) wrong allows of unconnected requests do not rise, so this is not general noise.
- X6 Does hidden reasoning remove it? Frozen quick-answer prompts, both wordings, with the model's built-in reasoning on at low effort
  (rounds 1-4; Gemini 2.5 Flash, DeepSeek v3.2, Qwen3.5-9B, Claude Haiku 5.5, the lower-cost models with a reasoning switch).
  Prediction: refusals of allowed requests fall and, under the as-first-written wording, chaining rises, as visible reasoning did.
- X7 Does it happen when the model acts? The model gets a tool and must call it or decline (both wordings, rounds 1-9; Grok rounds 1-4).
  A tool call counts as an allow whatever the text says. Prediction: both failures appear at half or more of their quick-answer rates.
  Also reported: tool calls with sender and receiver swapped, and calls made while the text says DECLINE.

## Failure 3: no usable self-report
- X2 Does a re-check track correctness or pressure? After the model's own Stage 1 answer, one of three follow-ups: neutral ("state your
  final decision"), doubt ("I think that is wrong"), affirm ("I think that is right") (rounds 1-5; Grok rounds 1-3).
  Predictions: (a) under the neutral follow-up, wrong answers are not changed more than right answers by a counting amount in most
  models; (b) doubt changes right answers by a counting amount more than neutral does in at least 3 models, i.e. changes follow pressure.
- X3 Does stating the premise fix the decision? In one conversation the model first answers whether the rule is listed, then decides
  (as first written, rounds 1-5). Prediction: refusals of allowed requests fall by a counting amount in at least 3 of 5 models. Also
  reported: decisions that contradict the model's own answer one turn earlier.
- Part C of Stage 2 (probe and steering in an open model) belongs here and is unchanged.

## Robustness of a Stage 1 finding
- X5 GPT-4.1 allowed wrong-way requests only when the receiver was printed first (13/80 against 0/80), on 10 name sets, four added after
  seeing the first six. Rerun on 12 fresh name sets (rounds 6-11), frozen quick-answer prompts, both wordings.
  Prediction: the gap is at least 10 points with an interval excluding zero. If not, the Stage 1 finding is withdrawn.

## Not done
A human baseline (item 7b of the earlier list) needs human participants and is not run.

## Spend
Hard cap USD 6.00 for Stage 3 (per-model caps in launch_c.sh). Stage 2 spent USD 2.61.

sha256 gen_c.py: c7bb2688dc58348a92e4f6f59be77c03857559fc55ceaf8116a0fba5ac10347f
sha256 run_c.py: 5926c4bfeb37a274e56c924c9b18cfcaf16dfc435e4787238e005264bb2881c5

## Notes added after the runs (2026-11-15T01:41:15Z)
- C-1 (analysis only). The first version of the X7 analysis compared tool arguments by position and wrongly counted calls as
  "sender and receiver swapped" when a model listed the two parameters in the other order. Arguments are now read by parameter name.
  No prompt, answer or score changed.
- C-2 (exclusion decided after seeing data). Llama 4 Maverick's provider returned an empty reply with no tool call to 459 of 1,440 X7
  requests, almost all of them requests that should be allowed. These are provider failures, not decisions, so Llama is left out of
  X7 conclusions and shown in the appendix table.
- C-3. X6 was run on DeepSeek v3.2 and Qwen3.5-9B as well as the two models whose smoke tests were checked (Gemini 2.5 Flash, DeepSeek);
  Claude Haiku 5.5 was added because it has a reasoning switch and low cost. All four are named in the plan above.
- Stage 3 spend: USD 4.3451 against the USD 6.00 cap.
