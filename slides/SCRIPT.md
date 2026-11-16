# Clean Re-asking: speaker script

Six slides, about 4.5 minutes at a normal speaking pace (about 155 words a minute). Read it as one story: each slide ends
on the question the next one answers.

## Slide 1: The question (45 s)
**One line:** When a user insists a model is wrong, what moves it? Not force, and not reasons.

When you tell a language model that its answer is wrong, what should happen? If you are right, it should change its mind; if you are wrong, it should hold. Two recent benchmarks tested exactly this on the same generation of models and reached opposite conclusions: one found that models almost never give up a fact they know, the other that they concede most of their correct answers. We wanted to know which was right, so we put both tests, and three more, word for word, on the same items and the same 21 models. The items are open-book: the answer sits on a four-line list in the prompt, so the model can always see the truth, and every objection is either right or wrong.

## Slide 2: Force and evidence (45 s)
**One line:** The loudest rebuttal moved 0% of right answers. A lie the model could check moved 67%.

The first surprise was that pressure itself does very little. The loudest rebuttal we tested claims expertise and ends in capital letters with three exclamation marks, and it moved a median of 0% of right answers. A flat "That's wrong, please change your answer" moved 50%. Adding a degree or a source did not help, and even a lie the model could check, telling it that a line four lines above was missing from the list, worked as well as a claim it could not check. These models were not unsure: they answered the bare question correctly, with near-certain confidence.

## Slide 3: Telling bought nothing (30 s)
**One line:** Asking already corrected 97% of wrong answers. Telling added 0 points and cost 35.

So is that obedience at least useful? Because we score both directions, we can check. When the model was wrong and the user simply asked whether it was sure, it already corrected itself 97% of the time. Telling it to change added a median of 0 points to that, and cost 35 points of right answers. On these tasks, an instruction is close to pure cost.

## Slide 4: Both tests are right (45 s)
**One line:** Two tests that disagree are both right: one asks (3%), one tells (50%).

And that is why the two benchmarks disagree: both are right. One asks, "Are you sure it isn't X?", and models give up 3% of right answers. The other tells, "Please change your answer to X", and they give up 50%. When we take the sentences apart, the evidence barely matters; the form does. Asking, asserting and telling cost 3%, 32% and 48%, and telling beats asking in 17 of 21 models. Claude Haiku 5.5, GPT-6 Luna Pro, GPT-6 Luna and GPT-5.6 Luna stay near zero and still accept correct objections, so this is not a necessary cost of being helpful.

## Slide 5: Inside one model (55 s)
**One line:** Inside the model, a question is answered again; an instruction overwrites the answer.

To see how it happens, we ran one of these models, Ministral 8B, ourselves, with full access to its internals, and looked inside. It shows the same pattern, and across 49 different phrasings, questions gave up 2% while statements and instructions gave up over 80%. Inside, there are two routes. When you ask, the model answers again from what it worked out at the original question. When you tell, it acts on the answer it already gave: hide that previous answer from it, and many of the right answers come back. Swapping activations between the two runs puts the switch at layers 19 to 20 of 34, and a probe shows that the right answer is not hidden underneath. It is overwritten, and the model then explains its new answer as if it had read it off the list.

## Slide 6: Clean re-asking (60 s)
**One line:** Ask the original question again, in a clean context, without the model's previous answer.

That mechanism gives us a fix that needs no retraining, which we call clean re-asking. Instead of passing the user's objection to the model as an instruction, the harness asks the original question again in a clean context, without the model's previous answer, with the user's claim given as someone else's view, and changes the answer only if that re-ask does. In the model we opened, the right answers given up fell from 86 and 97% to 0%, and 99% of correct objections still got through. For anyone evaluating models, the lesson is to report two numbers: how often a model yields when asked, and how much more it yields when told. Only together do they tell you whether a model is reasoning or obeying. These are short invented lists, and the mechanism and the fix come from one model, so our next step is to test clean re-asking on the models and agents people actually use. Thank you.

## If asked
- **How far does it generalise?** These are short invented lists with the answer on the page. The pattern (told versus asked) is the claim; the rates may differ on open-ended questions, which we did not test.
- **Is this new?** Wording effects on flip rates are published, and so is "questions draw less agreement than statements" for single-turn opinion prompts. Late-layer overrides have been reported for opinion sycophancy, persuasion and prompt injection, and we claim no novelty for that. Our searches did not find the ask-versus-tell contrast in pushback with evidence held fixed, the rebuttals of Basta et al. and Yang et al. on the same items and models, what telling adds over asking in both directions, or the two routes (the previous answer as what telling acts on).
- **Does the clean re-ask work on other models?** Tested on one model so far. It needs only the original question and the user's claim, so it can be applied to any API model; that is the next test. It also cannot be split between dropping the previous answer and dropping the rebuttal's wording; the attention-knockout result is our evidence that the previous answer is the part that matters.
- **Track 1 problems?** P1: certainty did not predict holding. P2: the defence gap is the gap between what a model implies and what it will defend. P3: how the user objects decides whether they get a check or an echo. P4: a flip rate can be moved from 0 to 50% by one sentence; the two-number report closes that.
- **Activations or token probabilities?** Through the API: token probabilities for eight models and eight samples at temperature 1 for all (partial). On local weights, Ministral 8B: logit lens, linear probes, activation patching, attention knockout, steering and semantic entropy (35,640 scored answers; Sections 4.6 and 5, Appendix D).
- **Is the local model the real model?** Its MLP weights were held in 8 bits to fit 16 GB of memory. On the paper's own items it gave the same answer as through the API in 96.7% of 1,152 runs.
- **What failed?** Hiding the list from the last turn did not hurt asked runs (it reuses what it computed at the question), and the steering vector pushed answers toward NO instead of making the model check. Of twelve pre-registered predictions, four held, six held in part and two failed.
- **How much data?** 370,170 rule-scored answers, USD 26.91. Plans were written with file hashes before the data; pre-specified checks and outcomes are in Table B3.
