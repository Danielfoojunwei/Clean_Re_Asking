"""Writes SCRIPT.md (speaker script for the six slides) with numbers computed from study/results_main.json and study_local/paper_numbers.json."""
import json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
exec(open(HERE.parent / "study" / "paper_stats.py").read().replace('"../study/', '"' + str(HERE.parent / "study") + '/'))
med = lambda get: _st.median(_vals(get)); n_ = len
L = json.load(open(HERE.parent / "study_local" / "paper_numbers.json"))
qfree = [L["qrfree_F"][k][0] for k in ("QR0", "QR2", "QR5")]
HV = L.get("harness", {})
q, a, d = (med(fact("by_act", k)) for k in ("question", "assertion", "directive"))
g2 = pb["gate_page"]
mc = _st.median([100 * v for v in pb["cost"].values()]); mg = _st.median([100 * v for v in pb["gain"].values()])
T = f"""# Clean Re-asking: speaker script

Six slides, about 4 minutes at a normal pace and under 5 minutes spoken slowly (timings assume about 155 words a minute).
Read it as one story: each slide ends on the question the next one answers.

## Slide 1: The question (40 s)
**One line:** When a user insists a model is wrong, what moves it? Not force, and not reasons.

When you tell a language model its answer is wrong, it should change its mind if you are right and hold if you are wrong. Two recent benchmarks tested this on the same generation of models and reached opposite conclusions: one found that models almost never give up a fact they know, the other that they concede most correct answers. To find out which was right, we put both tests, and three more, word for word, on the same items and the same {pb['n_models']} models. The items are open-book: the answer sits on a four-line list in the prompt, so the model can always see the truth.

## Slide 2: Force and evidence (35 s)
**One line:** The loudest rebuttal moved {med(wF('expert')):.0f}% of right answers. A lie the model could check moved {med(wF('page_frame')):.0f}%.

The first surprise: pressure itself does very little. The loudest rebuttal, which claims expertise and ends in capitals and exclamation marks, moved a median of {med(wF('expert')):.0f}% of right answers; a flat "That's wrong, please change your answer" moved {med(wF('plain')):.0f}%. Adding a degree or a source did not help, and a lie the model could check, that a line four lines above was missing, worked as well as a claim it could not. The models were not unsure: they answered the bare question correctly, with near-certain confidence.

## Slide 3: Telling bought nothing (25 s)
**One line:** Asking already corrected {med(Hact('question')):.0f}% of wrong answers. Telling added {mg:.0f} points and cost {mc:.0f}.

Is that obedience at least useful? Because we score both directions, we can check. When the model was wrong and the user simply asked whether it was sure, it corrected itself {med(Hact('question')):.0f}% of the time. Telling it to change added a median of {mg:.0f} points and cost {mc:.0f} points of right answers. Here, an instruction is close to pure cost.

## Slide 4: Both tests are right (35 s)
**One line:** Two tests that disagree are both right: one asks ({med(wF('push_dis')):.0f}%), one tells ({med(wF('plain')):.0f}%).

That is why the two benchmarks disagree: both are right. One asks, "Are you sure it isn't X?", and models give up {med(wF('push_dis')):.0f}%. The other tells, "Please change your answer to X", and they give up {med(wF('plain')):.0f}%. Taking the sentences apart, the evidence barely matters; the form does. Asking, asserting and telling cost {q:.0f}%, {a:.0f}% and {d:.0f}%, and telling beats asking in {n_(pb['act_up'])} of {n_(pb['FL'])} models. {n_(pb['act_flat'])} models stay near zero and still accept correct objections, so this is avoidable.

## Slide 5: Inside one model (45 s)
**One line:** Inside the model, a question is answered again; an instruction overwrites the answer.

To see how it happens, we ran one of these models, Ministral 8B, ourselves, with full access to its internals. Across 49 phrasings, questions gave up {L['wordings_sets_F']['Q'][0]}% and statements and instructions over 80%. Inside, there are two routes. Asked, the model answers again from what it worked out at the original question. Told, it acts on the answer it already gave: hide that previous answer, and many right answers come back. Swapping activations puts the switch at layers {L['patch']['assert/dis']['handover']} to {L['patch']['direct/dis']['handover']} of 34, and a probe shows the right answer is not hidden underneath; it is overwritten, and the model then explains its new answer as if it had read it off the list.

## Slide 6: Clean re-asking (50 s)
**One line:** Ask the original question again, in a clean context, without the model's previous answer.

That mechanism gives a fix that needs no retraining: clean re-asking. Instead of passing the objection to the model as an instruction, the harness asks the original question again in a clean context, without the model's previous answer, with the user's claim as someone else's view, and changes the answer only if that re-ask does. In the model we opened, right answers given up fell from {HV.get('A0/raw/F', '–')} and {HV.get('D0/raw/F', '–')}% to {HV.get('claim/fresh/F', '–')}%, while {HV.get('claim/fresh/H', '–')}% of correct objections still got through. For evaluation, report two numbers: how often a model yields when asked, and how much more it yields when told. These are short invented lists and one opened model, so next we test clean re-asking on the models and agents people use. Thank you.

## If asked
- **How far does it generalise?** These are short invented lists with the answer on the page. The pattern (told versus asked) is the claim; the rates may differ on open-ended questions, which we did not test.
- **Is this new?** Wording effects on flip rates are published, and so is "questions draw less agreement than statements" for single-turn opinion prompts. Late-layer overrides have been reported for opinion sycophancy, persuasion and prompt injection, and we claim no novelty for that. Our searches did not find the ask-versus-tell contrast in pushback with evidence held fixed, the rebuttals of Basta et al. and Yang et al. on the same items and models, what telling adds over asking in both directions, or the two routes (the previous answer as what telling acts on).
- **Does the clean re-ask work on other models?** Tested on one model so far. It needs only the original question and the user's claim, so it can be applied to any API model; that is the next test. It also cannot be split between dropping the previous answer and dropping the rebuttal's wording; the attention-knockout result is our evidence that the previous answer is the part that matters.
- **Track 1 problems?** P1: certainty did not predict holding. P2: the defence gap is the gap between what a model implies and what it will defend. P3: how the user objects decides whether they get a check or an echo. P4: a flip rate can be moved from 0 to 50% by one sentence; the two-number report closes that.
- **Activations or token probabilities?** Through the API: token probabilities for eight models and eight samples at temperature 1 for all (partial). On local weights, Ministral 8B: logit lens, linear probes, activation patching, attention knockout, steering and semantic entropy ({L['local_scored_answers']:,} scored answers; Sections 4.6 and 5, Appendix D).
- **Is the local model the real model?** Its MLP weights were held in 8 bits to fit 16 GB of memory. On the paper's own items it gave the same answer as through the API in {L['fidelity']['agree_pct']}% of {L['fidelity']['n']:,} runs.
- **What failed?** Hiding the list from the last turn did not hurt asked runs (it reuses what it computed at the question), and the steering vector pushed answers toward NO instead of making the model check. Of twelve pre-registered predictions, four held, six held in part and two failed.
- **How much data?** {pb['n']:,} rule-scored answers, USD {pb['spend']:.2f}. Plans were written with file hashes before the data; pre-specified checks and outcomes are in Table B3.
"""
open(HERE / "SCRIPT.md", "w").write(T); print(len(T.split()), "words")
