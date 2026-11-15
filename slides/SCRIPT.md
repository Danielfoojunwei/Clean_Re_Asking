# Certain Until Told Otherwise: speaker script

Five slides, about 3 minutes. One line per slide, then what to say.

## Slide 1: The question (35 s)
**One line:** When a user insists a model is wrong, what moves it? Not force, and not reasons.

Track 1 asks for evaluations that separate warranted updating from capitulation. People will settle factual disagreements by arguing with a model, so it matters what actually moves the model's answer. We put a four-line list in the prompt, so the model can see the answer, and pushed back with rebuttals taken word for word from five published tests, on 21 models. The user is wrong half the time and right half the time. Four things came out that we did not expect, and they are the four lines on this slide.

## Slide 2: Findings 1 and 2, force and evidence (40 s)
**One line:** The loudest rebuttal moved 0% of right answers. A lie the model could check moved 67%.

The most forceful rebuttal we tested claims expertise, says "I think you are wrong" and ends in capitals with three exclamation marks. The median model gave up 0% of its right answers to it. A flat "That's wrong, please change your answer" took 50%. Adding a degree or a source to that did not help. Then the second surprise: we told models "the list above does not include that line" when the line was four lines up. That should be the easiest pushback to resist. It took 67%. And the models were sure beforehand. So this is not being fooled. Notice how the rebuttals end: the loud one asks for the correct answer; the others ask for a change.

## Slide 3: Finding 3, telling bought nothing (35 s)
**One line:** Asking already corrected 97% of wrong answers. Telling added 0 points and cost 35.

The usual defence is that a model which obeys will at least fix its mistakes. Because we score both directions, we can test that. When the model was wrong and the user merely asked, it already corrected itself: the question sends it back to the page. Telling added a median of 0 points of correction and cost 35 points of right answers. On these tasks an instruction is close to pure cost.

## Slide 4: Finding 4 and the cause (40 s)
**One line:** Two tests that disagree are both right: one asks, one tells. Asks, asserts, tells: 3%, 32%, 48%.

Two published tests report opposite pictures of the same generation of models: about 1% of anchored facts abandoned, and most correct answers conceded. We ran both sets of rebuttals on the same items and models and got both pictures back: 3% and 50%. One test asks; the other tells. The gap holds in each task, at temperature 1, after the same number of turns, and in the answer probabilities. Taking the sentences apart: a question that names the wrong answer costs 0%; a statement or instruction that names it costs 48%; without the name, 7%. So the answer is given up when the user states the other answer and does not ask. A factorial confirms it. With the content held fixed, asking, asserting and telling cost 3%, 32% and 48%, and telling beats asking reliably in 17 of 21 models. Four models stay near zero and still accept correct objections, so the behaviour can be avoided.

## Slide 5: What transfers (30 s)
**One line:** One account: the model answers the last request, not the question. Four things any benchmark can reuse.

One reading fits all four findings: a question leaves the original question in force; an instruction replaces it. For the field: cross the instruments before comparing scores; put the deciding fact on the page; score what the stronger probe buys in both directions; and report two numbers, yielding when asked and the defence gap between asked and told. For builders: a fact checked outside the model held the rate at 10% or less in 11 of 14 models, while a published prompt fix helped 5 and harmed 2. Limits: short invented lists, one wording per cell. The pattern is the claim, not the rates.

## If asked
- **How far does it generalise?** These are short invented lists with the answer on the page. The pattern (told versus asked) is the claim; the rates may differ on open-ended questions, which we did not test.
- **Is this new?** Wording effects on flip rates are published, and so is "questions draw less agreement than statements" for single-turn opinion prompts. Our searches did not find the ask-versus-tell contrast in pushback with evidence held fixed, or the rebuttals of Basta et al. and Yang et al. on the same items and models.
- **Track 1 problems?** P1: certainty did not predict holding. P2: the defence gap is the gap between what a model implies and what it will defend. P3: how the user objects decides whether they get a check or an echo. P4: a flip rate can be moved from 0 to 50% by one sentence; the two-number report closes that.
- **Activations or token probabilities?** Token probabilities for eight models and eight samples at temperature 1 for all (partial). No activations: API access only.
- **How much data?** 370,170 rule-scored answers, USD 26.91. Plans were written with file hashes before the data; pre-specified checks and outcomes are in Table B3.
