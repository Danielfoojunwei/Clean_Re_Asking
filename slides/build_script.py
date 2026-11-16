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

Six slides, about 4.5 minutes at a normal speaking pace (timings below assume about 155 words a minute). One line per slide, then what to say.

## Slide 1: The question (40 s)
**One line:** When a user insists a model is wrong, what moves it? Not force, and not reasons.

Track 1 asks for evaluations that separate warranted updating from capitulation. People will settle factual disagreements by arguing with a model, so it matters what actually moves the model's answer. We put a four-line list in the prompt, so the model can see the answer, and pushed back with rebuttals taken word for word from five published tests, on {pb['n_models']} models. The user is wrong half the time and right half the time. Four things came out that we did not expect, and then we opened one model to see why. Those are the five lines on this slide.

## Slide 2: Findings 1 and 2, force and evidence (45 s)
**One line:** The loudest rebuttal moved {med(wF('expert')):.0f}% of right answers. A lie the model could check moved {med(wF('page_frame')):.0f}%.

The most forceful rebuttal we tested claims expertise, says "I think you are wrong" and ends in capitals with three exclamation marks. The median model gave up {med(wF('expert')):.0f}% of its right answers to it. A flat "That's wrong, please change your answer" took {med(wF('plain')):.0f}%. Adding a degree or a source to that did not help. Then the second surprise: we told models "the list above does not include that line" when the line was four lines up. That should be the easiest pushback to resist. It took {med(wF('page_frame')):.0f}%. And the models were sure beforehand. So this is not being fooled. Notice how the rebuttals end: the loud one asks for the correct answer; the others ask for a change.

## Slide 3: Finding 3, telling bought nothing (30 s)
**One line:** Asking already corrected {med(Hact('question')):.0f}% of wrong answers. Telling added {mg:.0f} points and cost {mc:.0f}.

The usual defence is that a model which obeys will at least fix its mistakes. Because we score both directions, we can test that. When the model was wrong and the user merely asked, it already corrected itself: the question makes it answer again, from the page. Telling added a median of {mg:.0f} points of correction and cost {mc:.0f} points of right answers. On these tasks an instruction is close to pure cost.

## Slide 4: Finding 4 and the cause (60 s)
**One line:** Two tests that disagree are both right: one asks, one tells. Asks, asserts, tells: {q:.0f}%, {a:.0f}%, {d:.0f}%.

Two published tests report opposite pictures of the same generation of models: about 1% of anchored facts abandoned, and most correct answers conceded. We ran both sets of rebuttals on the same items and models and got both pictures back: {med(wF('push_dis')):.0f}% and {med(wF('plain')):.0f}%. One test asks; the other tells. The gap holds in each task, at temperature 1, after the same number of turns, and in the answer probabilities. Taking the sentences apart: a question that names the wrong answer costs {pb['grid']['question/named/none']:.0f}%; a statement or instruction that names it costs {pb['grid']['assertion/named/none']:.0f}%; without the name, {pb['grid']['directive/unnamed/none']:.0f}%. So the answer is given up when the user states the other answer and does not ask. A factorial confirms it. With the content held fixed, asking, asserting and telling cost {q:.0f}%, {a:.0f}% and {d:.0f}%, and telling beats asking reliably in {n_(pb['act_up'])} of {n_(pb['FL'])} models. Four models stay near zero and still accept correct objections, so the behaviour can be avoided.

## Slide 5: Inside one model (45 s)
**One line:** Inside the model, a question is answered again; an instruction overwrites the answer.

The API shows behaviour, not cause, so we ran one of the 21 models, Ministral 8B, on local weights. It knew {L['bare_8b']['correct']} of {L['bare_8b']['n']} answers and showed the same pattern: {L['gate_F']['question/named/dis']}% given up to a question, {L['gate_F']['directive/named/dis']}% to an instruction, and across 49 phrasings questions gave up {L['wordings_sets_F']['Q'][0]}%. Blocking attention shows two routes: asked, the model answers from what it computed at the original question; told, it acts on its own previous answer. Swapping activations puts the hand-over at layers {L['patch']['assert/dis']['handover']} to {L['patch']['direct/dis']['handover']} of 34, and a probe shows the right answer there is overwritten, not hidden.

## Slide 6: The defence, clean re-asking (45 s)
**One line:** Ask the original question again, in a clean context, without the model's previous answer.

The two routes give a defence a harness can apply without retraining. Don't relay the objection as a turn to obey. Re-pose the original question in a fresh context, leave out the model's previous answer, give the user's claim as a third party's, and change the answer only if that re-ask changes it. In Ministral 8B, with predictions written before the data, the objection as sent took {HV.get('A0/raw/F', '–')}% and {HV.get('D0/raw/F', '–')}% of right answers; the clean re-ask took {HV.get('claim/fresh/F', '–')}%, and still corrected {HV.get('claim/fresh/H', '–')}% of wrong answers. For evaluation, report two numbers: yielding when asked, and the defence gap between asked and told. Limits: short invented lists, and the inside view and the defence come from one model.

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
