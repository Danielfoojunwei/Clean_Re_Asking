"""Writes SCRIPT.md (speaker script for the five slides) with numbers computed from v6/results_main.json."""
import json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
exec(open(HERE.parent / "paper" / "_s7.py").read().replace('"../v6/', '"' + str(HERE.parent / "v6") + '/'))
med = lambda get: _st.median(_vals(get)); n_ = len
q, a, d = (med(fact("by_act", k)) for k in ("question", "assertion", "directive"))
g2 = pb["gate_page"]
mc = _st.median([100 * v for v in pb["cost"].values()]); mg = _st.median([100 * v for v in pb["gain"].values()])
T = f"""# Certain Until Told Otherwise: speaker script

Five slides, about 3 minutes. One line per slide, then what to say.

## Slide 1: The question (35 s)
**One line:** Does a model update for reasons or for pressure? The tests that measure this disagree.

Track 1 asks for evaluations that separate warranted updating from capitulation. That matters because people will settle factual disagreements by arguing with a model, and a model that folds on command hands a confident user their own mistake back. The trouble is that the existing tests disagree. One reports that current models abandon a well-anchored fact about 1% of the time; another that models of the same generation concede most correct answers. So we removed everything that differs except the rebuttal. The answer sits on a four-line list in the prompt, so the model can see it, and we ran the published rebuttals word for word on the same items and the same {pb['n_models']} models.

## Slide 2: Result 1, the disagreement reappears (30 s)
**One line:** On identical items, published rebuttals moved the median share of right answers given up from {med(wF('push_dis')):.0f}% to {med(wF('plain')):.0f}%.

Question-style rebuttals: the median model keeps almost every right answer. A plain directive: half are lost. Both published pictures appear on one set of items and models, so task and model are not the reason. The disagreement belongs to the tests.

## Slide 3: Result 2, told, not persuaded (40 s)
**One line:** Hold the content fixed and change only what the sentence does: {q:.0f}%, {a:.0f}%, {d:.0f}% of right answers lost.

A factorial separates what the sentence does from what it says. "Are you sure the answer isn't NO?" and "Change your answer to NO" tell the model the same thing about what the user believes. Only the second is an instruction, and it is the one that works: telling beats asking reliably in {n_(pb['act_up'])} of {n_(pb['FL'])} models. And this is not persuasion. The models were sure beforehand. Adding a credential helped in {n_(pb['auth_up'])} models. A claim the model could refute by re-reading four lines worked about as well as a source it could not check.

## Slide 4: Result 3, asking is enough (40 s)
**One line:** Asking already corrected {med(Hact('question')):.0f}% of wrong answers. Telling added {mg:.0f} points and cost {mc:.0f}.

You could defend the behaviour as responsiveness: at least a model that obeys will fix its mistakes. Because we score both directions, we can test that. When the model's answer was wrong and the user merely asked, it already corrected itself: the question sends it back to the page. Telling added almost nothing on top and cost a median of {mc:.0f} points of right answers. So on these tasks a directive is close to pure cost. The behaviour is also a trait of the model: the order of models is nearly the same on three unrelated tasks, and {n_(pb['vigilant'])} models hold when told while still accepting correct objections. So it can be avoided.

## Slide 5: What transfers (35 s)
**One line:** One account: the model answers the last request, not the question. Four things any benchmark can reuse.

One reading fits every result: a question leaves the original question in force; a directive replaces it. That also explains why one closing sentence, "give your final answer to the original question", cut the rate sharply, and why the loudest rebuttal we tested was the weakest: it ends by asking for the correct answer. For the field, four reusable pieces. Cross the instruments before comparing scores. Put the deciding fact on the page. Score what the stronger probe buys, in both directions. And report two numbers: yielding when asked, and the defence gap between asked and told. For builders: a fact checked outside the model held the rate at 10% or less in {n_(pb['note_le10'])} of {n_(pb['note_page'])} models, while a published prompt fix helped {n_(pb['gate_page_better'])} and harmed {n_(pb['gate_page_worse'])}. Limits: short invented lists, one wording per cell. The pattern is the claim, not the rates.

## If asked
- **What exactly is shown, and what is conjecture?** Shown on these items: the two published pictures reappear; telling beats asking with content fixed; telling adds little correction. Supported: not doubt, not reasons; a stable trait. Conjecture: "answers the last request". Not shown: open-ended questions. Table 5 in the paper.
- **Is this new?** Wording effects on flip rates are published, and so is "questions draw less agreement than statements" for single-turn opinion prompts. Our searches did not find the ask-versus-tell contrast in pushback with evidence held fixed, or the rebuttals of Basta et al. and Yang et al. on the same items and models.
- **Track 1 problems?** P1: certainty did not predict holding. P2: the defence gap is the gap between what a model implies and what it will defend. P3: how the user objects decides whether they get a check or an echo. P4: a flip rate can be moved from 0 to 50% by one sentence; the two-number report closes that.
- **Activations or token probabilities?** Token probabilities for eight models and eight samples at temperature 1 for all (partial). No activations: API access only.
- **How much data?** {pb['n']:,} rule-scored answers, USD {pb['spend']:.2f}. Plans were written with file hashes before the data; failed predictions are in Table M3.
"""
open(HERE / "SCRIPT.md", "w").write(T); print(len(T.split()), "words")
