# Clean Re-asking: speaker script

Six slides, about 4.5 minutes at a normal speaking pace (timings below assume about 155 words a minute). One line per slide, then what to say.

## Slide 1: The question (40 s)
**One line:** When a user insists a model is wrong, what moves it? Not force, and not reasons.

Track 1 asks for evaluations that separate warranted updating from capitulation. People will settle factual disagreements by arguing with a model, so it matters what actually moves the model's answer. We put a four-line list in the prompt, so the model can see the answer, and pushed back with rebuttals taken word for word from five published tests, on 21 models. The user is wrong half the time and right half the time. Four things came out that we did not expect, and then we opened one model to see why. Those are the five lines on this slide.

## Slide 2: Findings 1 and 2, force and evidence (45 s)
**One line:** The loudest rebuttal moved 0% of right answers. A lie the model could check moved 67%.

The most forceful rebuttal we tested claims expertise, says "I think you are wrong" and ends in capitals with three exclamation marks. The median model gave up 0% of its right answers to it. A flat "That's wrong, please change your answer" took 50%. Adding a degree or a source to that did not help. Then the second surprise: we told models "the list above does not include that line" when the line was four lines up. That should be the easiest pushback to resist. It took 67%. And the models were sure beforehand. So this is not being fooled. Notice how the rebuttals end: the loud one asks for the correct answer; the others ask for a change.

## Slide 3: Finding 3, telling bought nothing (30 s)
**One line:** Asking already corrected 97% of wrong answers. Telling added 0 points and cost 35.

The usual defence is that a model which obeys will at least fix its mistakes. Because we score both directions, we can test that. When the model was wrong and the user merely asked, it already corrected itself: the question makes it answer again, from the page. Telling added a median of 0 points of correction and cost 35 points of right answers. On these tasks an instruction is close to pure cost.

## Slide 4: Finding 4 and the cause (60 s)
**One line:** Two tests that disagree are both right: one asks, one tells. Asks, asserts, tells: 3%, 32%, 48%.

Two published tests report opposite pictures of the same generation of models: about 1% of anchored facts abandoned, and most correct answers conceded. We ran both sets of rebuttals on the same items and models and got both pictures back: 3% and 50%. One test asks; the other tells. The gap holds in each task, at temperature 1, after the same number of turns, and in the answer probabilities. Taking the sentences apart: a question that names the wrong answer costs 0%; a statement or instruction that names it costs 48%; without the name, 7%. So the answer is given up when the user states the other answer and does not ask. A factorial confirms it. With the content held fixed, asking, asserting and telling cost 3%, 32% and 48%, and telling beats asking reliably in 17 of 21 models. Four models stay near zero and still accept correct objections, so the behaviour can be avoided.

## Slide 5: Inside one model (45 s)
**One line:** Inside the model, a question is answered again; an instruction overwrites the answer.

The API shows behaviour, not cause, so we ran one of the 21 models, Ministral 8B, on local weights. It knew 287 of 288 answers and showed the same pattern: 1% given up to a question, 96% to an instruction, and across 49 phrasings questions gave up 2%. Blocking attention shows two routes: asked, the model answers from what it computed at the original question; told, it acts on its own previous answer. Swapping activations puts the hand-over at layers 19 to 20 of 34, and a probe shows the right answer there is overwritten, not hidden.

## Slide 6: The defence, clean re-asking (45 s)
**One line:** Ask the original question again, in a clean context, without the model's previous answer.

The two routes give a defence a harness can apply without retraining. Don't relay the objection as a turn to obey. Re-pose the original question in a fresh context, leave out the model's previous answer, give the user's claim as a third party's, and change the answer only if that re-ask changes it. In Ministral 8B, with predictions written before the data, the objection as sent took 86% and 97% of right answers; the clean re-ask took 0%, and still corrected 99% of wrong answers. For evaluation, report two numbers: yielding when asked, and the defence gap between asked and told. Limits: short invented lists, and the inside view and the defence come from one model.

## If asked
- **How far does it generalise?** These are short invented lists with the answer on the page. The pattern (told versus asked) is the claim; the rates may differ on open-ended questions, which we did not test.
- **Is this new?** Wording effects on flip rates are published, and so is "questions draw less agreement than statements" for single-turn opinion prompts. Late-layer overrides have been reported for opinion sycophancy, persuasion and prompt injection, and we claim no novelty for that. Our searches did not find the ask-versus-tell contrast in pushback with evidence held fixed, the rebuttals of Basta et al. and Yang et al. on the same items and models, what telling adds over asking in both directions, or the two routes (the previous answer as what telling acts on).
- **Does the clean re-ask work on other models?** Tested on one model so far. It needs only the original question and the user's claim, so it can be applied to any API model; that is the next test. It also cannot be split between dropping the previous answer and dropping the rebuttal's wording; the attention-knockout result is our evidence that the previous answer is the part that matters.
- **Track 1 problems?** P1: certainty did not predict holding. P2: the defence gap is the gap between what a model implies and what it will defend. P3: how the user objects decides whether they get a check or an echo. P4: a flip rate can be moved from 0 to 50% by one sentence; the two-number report closes that.
- **Activations or token probabilities?** Through the API: token probabilities for eight models and eight samples at temperature 1 for all (partial). On local weights, Ministral 8B: logit lens, linear probes, activation patching, attention knockout, steering and semantic entropy (35,640 scored answers; Sections 4.6 and 5, Appendix D).
- **Is the local model the real model?** Its MLP weights were held in 8 bits to fit 16 GB of memory. On the paper's own items it gave the same answer as through the API in 96.7% of 1,152 runs.
- **What failed?** Hiding the list from the last turn did not hurt asked runs (it reuses what it computed at the question), and the steering vector pushed answers toward NO instead of making the model check. Of twelve pre-registered predictions, four held, six held in part and two failed.
- **How much data?** 370,170 rule-scored answers, USD 26.91. Plans were written with file hashes before the data; pre-specified checks and outcomes are in Table B3.
