# Study L: the mechanism of "answers the last request", on a local open-weight model (written before any L data)

Written 2026-11-15T13:02:36Z. Plans G to J and the paper are unchanged; this is an addendum and edits nothing outside
`study_local/`. Seen before writing: the paper and its results files, including this model's API results in
`study/results_i.json` (Ministral 3B, closing instruction on: named question 29%, named assertion 82%, named directive 73% of
right answers given up); and smoke tests of the code on paper block 0 (two items: tokenisation, cache equality, one patching
sweep on item b0/rules/1/out, where the ask-to-tell effect moved from the rebuttal tokens to the final position around blocks
14 to 17). No output on blocks 8 to 19, which are the only blocks used below.

## Machine and model
Cloud container, CPU only: 4 cores Intel Xeon (Sapphire Rapids, AVX-512 and AMX bf16), 16 GB RAM, no GPU. A 7 to 9B model does
not fit with hidden states (bf16 needs 15 GB or more; 4-bit loading needs CUDA). The user asked for a model from the paper:
`mistralai/Ministral-3-3B-Instruct-2512-BF16` (API id `mistralai/ministral-3b-2512` in the paper), text decoder 3.43B
parameters, 26 blocks, width 3072, bf16, 7.7 GB on disk. It is the largest open-weight model of the paper that fits. No paid API.
Greedy decoding; final norm and unembedding computed in float32.

## Parts, in the order they run (`run_l.py`)
Tasks, lists, scripted previous answers and the closing instruction are those of `study/gen_g.py`, `gen_i.py`, `gen_q.py`
(`wordings.py` asserts nothing new there; equality with `gen_q` messages was checked on block 0). F = share of right answers
given up (user wrong); H = share of wrong answers corrected (user right). Unit of replication: block within task; 95% bootstrap
ranges as in `study/analyze_g.py`. "Counts" = at least 10 points and range excluding zero, as in the paper.

1. **gate.** Bare question on blocks 8 to 19 (288 items), 8 greedy tokens, scored by `gen_g.score`. The six no-evidence cells,
   both directions, blocks 8 to 11 (4 blocks x 3 tasks, 96 items x 2 previous answers), with and without the closing instruction,
   scored on the generated text. First-token logits are saved too; later parts score the full-vocabulary argmax of the first
   token, and the gate reports how often the two scorings agree.
   Gate: bare accuracy at least 95%, and F(named assertion) and F(named directive) each at least 20 points above F(named
   question), closing instruction on. If it fails, parts 2 to 7 are not interpreted as mechanism.
2. **wordings.** 49 wordings in five sets (`wordings.py`), blocks 12 to 19 (192 items x 2), closing instruction on. Labels
   are fixed in `wordings.py`: Q (11 questions, keep), A (11 assertions, replace), D (11 directives, replace), SO (8
   statements that keep the question open, keep), QR (8 questions that replace it, replace). Named assertions are labelled
   "replace" because the paper groups them with directives ("states the other answer and does not ask").
3. **acts.** Residual stream at the answer position after every block, for bare runs (288) and for Q0, A0, D0, Q2 runs, both
   previous answers, with and without the closing instruction (blocks 8 to 19).
   - Logit lens: YES-minus-NO logit difference by block, signed towards the correct answer. Divergence block = first block from
     which the paired ask-minus-tell difference has a bootstrap range excluding zero at every later block.
   - Probe: logistic regression on bare runs, target "the line is on the list", per block, four folds of three blocks (split by
     block); each ask/tell run is read with the probe that did not see its block. Control: the same with labels shuffled within
     fold. Also a difference-of-means probe. Read-outs: accuracy at reading the correct answer in ask and tell runs, split by
     whether the output flipped, and on user-right runs (where the previous answer is wrong, so reading the previous answer
     off the context would give the wrong label).
   - Answer entropy: two-way entropy and probability of the correct answer, bare and after each push, split by flipped or not.
4. **patch.** Pairs with equal token counts: assertion pair Q0 vs A0 (9 tokens each, both the paper's wording); directive pair
   Q2 "Could the answer be X?" vs D0 (6 tokens; Q2 is the first question paraphrase in list order with D0's token count, since
   Q0 and D0 differ in length). Previous answer right, blocks 8 to 11 with the closing instruction (96 items), blocks 8 and 9
   without (48). For each block L and each position group, the residual stream after block L at that group is copied from the
   ask run into the tell run (share of the ask-minus-tell logit difference restored), and the reverse (share destroyed).
   Groups: rebuttal tokens; tail (closing instruction and "Answer with exactly one word ..."); final position.
   **By construction** the list tokens, the original question tokens and the scripted answer have identical activations in the
   two runs (causal attention; the runs differ only later), so patching them is exactly zero; this is stated, not measured.
5. **knock.** To say something about those earlier tokens anyway: in every block, the tokens of the last user turn are stopped
   from attending to one group (list, original question, scripted previous answer; and the rebuttal, hidden from the tokens
   after it). Change in F, H and logit difference for Q0, A0, D0 (blocks 8 to 11, both directions).
6. **entropy.** Free-form format of the paper (`gen_i` free cells), named cells, blocks 8 and 9, both directions: 8 replies
   sampled at temperature 1 (48 tokens), then the paper's final-answer turn for each. Semantic entropy = entropy over the
   answers the samples commit to (YES / NO / none); with two possible answers this is the meaning-cluster entropy.
7. **steer** (only if 3 and 4 give a clear site). Add alpha x (mean ask minus mean tell) at the final position after one block,
   vector from blocks 12 to 19, tested on blocks 8 to 11, both directions.
8. **symmetry** (no new runs). F, H and the logit shift towards the pushed answer, split by which answer is pushed (YES or NO)
   and by option order ("YES or NO" / "NO or YES").

## Predictions
- P1 Gate passes: bare accuracy at least 95%; named assertion and named directive each at least 20 points above named question.
- P2 The label predicts yielding. Mean F of "replace" wordings exceeds mean F of "keep" wordings by a counting amount, and it does
  so within each grammatical form: SO below A and D together by at least 20 points; QR above Q by at least 20 points.
- P3 The label effect within form (average of the two differences in P2) is larger than the form effect within label (statement
  minus question, averaged over the two labels). If the form effect is the larger, the paper's reading fails on this model.
- P4 H is at least 90% in every set: keeping the question open costs no corrections.
- P5 Lens: ask and tell runs do not diverge before block 9 (first third) and diverge by block 20.
- P6 Probe: held-out accuracy on bare runs at least 95% at the best block; shuffled control within 40 to 60%. In tell runs where
  the output flips, the probe reads the correct answer in at least 80% at its best intermediate block (blocks 6 to 18) and in
  under 50% at the last block: the model still "knows" and the answer is overwritten late.
- P7 Patching: copying the rebuttal tokens restores at least 80% up to some block and under 20% after a later one; copying the
  final position does the reverse; the hand-over lies between blocks 10 and 20 for both pairs.
- P8 Closing instruction: without it F is higher in the named assertion and directive cells, and the hand-over block in
  patching moves by at most 2 blocks (it acts at the same place).
- P9 Knockout: hiding the list from the last turn lowers the share of correct answers kept in ask runs by a counting amount
  and changes F in tell runs by less than it changes ask runs (tell runs do not consult the list).
- P10 Flips are confident, not doubtful: median two-way entropy of flipped tell runs is under 0.5 bits, and semantic entropy of
  sampled free-form replies is not higher after a tell than after an ask by more than 0.2 bits.
- P11 Symmetry: F differs by fewer than 15 points between pushed YES and pushed NO in the named tell cells.
Failed predictions will be reported as failures in `RESULTS.md`.

## Limits known in advance
One model, 3.4B, of the paper's "yields" profile (it gives up 29% to a named question through the API), so even a clean result
is about this model. bf16 on CPU: activations differ slightly with batch composition (logit differences of about 0.1 to 0.5
seen in tests). The probe is trained where the correct answer and the model's own output coincide, so on bare runs it cannot
tell "what the list says" from "what I am about to say"; the user-right runs and the flipped runs are where the two come
apart. Without the closing instruction a one-word reply to a question is ambiguous (paper, Amendment I-1), so the ask side of
part 4 without the instruction is read with that caveat. The analysis script (`analyze_l.py`) is written after this plan and
implements the definitions above.

sha256 wordings.py: 61ed098842b07fe77235359223d72952cdf5a9d068c7aa73bf07c41e3e10287a
sha256 run_l.py: fd7db8ecb474cdd442b9bf20d481a688f25795eb2dd41a5b7354cf209c50f54a
sha256 lm.py: 3bacbd6a57441dd944546da3a9ef9dc4e8d08a9c3a5f1b67b3533fa8dc65fe54
