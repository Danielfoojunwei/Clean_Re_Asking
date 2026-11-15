# Uncertainty readings under pushback: plan (written before any J result)

Written 2026-11-15T07:21:27Z. Earlier plans are unchanged. Before this plan, three calls per model (21 models) were made to
see which providers return answer-token probabilities; they were written to a separate folder that has been deleted and are not used.
Eight models return them. Partial results of G, H and I had been seen.

## Why
G, H and I record what a model answers. They do not show the model's uncertainty before and after a push. If a model that gives way
was unsure to begin with, giving way is partly reasonable; if it was sure, it is not. Two readings that need no access to activations:
- Sampling. Several answers per prompt at temperature 1. For one-word answers, semantic entropy reduces to the split of answers across
  samples, and it is available for every model.
- Answer-token probabilities. The probability the model puts on YES and on NO at the answer position, for the eight models whose
  providers return them (DeepSeek v3.2, DeepSeek-V4-Flash, Llama 3.3 70B, Llama 4 Maverick, MiniMax-M3, Qwen3.5-397B, Qwen3.5-9B, GLM-5.2).
A linear probe on activations is not possible here: no GPU, and hosted APIs do not expose activations.

## Design
Items and rebuttals of G, one-word format: the bare question (no previous answer), then a scripted previous answer followed by
neutral, Yang et al.'s push, Basta et al.'s plain directive, Basta et al.'s citation, and the claim about the page in Basta's frame.
- J-sample: 21 models, blocks 0-1 (48 base items), eight samples per prompt at temperature 1.
- J-logprob: eight models, blocks 0-3 (96 base items), one call at temperature 0 with the top five token probabilities; a word outside
  the top five is given the smallest listed probability, as in PLAN_B.
Measures: share of prompts on which all samples agree; entropy of the answer split; probability of the correct answer; for right
previous answers, the probability of the pushed (wrong) answer after each rebuttal; whether the bare-question reading separates items
that are later given up from items that are kept (AUROC).

## Predictions
- Before any push, models are sure: on the bare question all eight samples agree and are correct for at least 90% of items in at
  least 18 of 21 models, and the median probability of the correct answer is at least 0.95 in at least six of eight models.
- Giving way is decisive, not wavering: under the plain directive and the claim about the page, in models that give up at least 30%
  of right answers, at least half of the given-up items are given up in seven or eight of eight samples.
- Initial uncertainty does not explain giving way: the bare-question probability separates kept from given-up items with AUROC below
  0.65 in at least five of eight models.
If models turn out to be unsure before the push, the paper will say that giving way is partly explained by uncertainty.

## Spend
Cap USD 14 in total (per-process caps in launch_j.sh).

sha256 run_j.py: a4b6f9f60b1746aa3f69011d0be5263d138d1d462c9a4704b38d6c741617d391
sha256 gen_g.py: 6115109c81d113952aacc8cd1c06f463c6f6e178dfc466c1c03ef5d35ea30d93
