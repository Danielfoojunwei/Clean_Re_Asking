# One Score, Three Failures: speaker script

Five slides, about 2 minutes 30 seconds. One line per slide, then what to say.

## Slide 1: The problem (30 s)
**One line:** One accuracy score on permission rules hides three different failures.

Here is a rulebook: Finance may send records to Legal, Legal to Audit, and so on. Only the listed directions are allowed. We normally test an AI on rules like this and report one score. We asked nine models the same questions eight different ways, 165,220 answers in total, with the plan fixed in advance. That one score turned out to be three separate problems.

## Slide 2: Failure 1, chaining (30 s)
**One line:** Models join rules into chains, and one sentence stops it.

Finance may send to Legal, and Legal may send to Audit. Many models conclude Finance may send to Audit. When they reason step by step, they wrongly allow 44% of these requests. Add one sentence saying routes cannot be chained, and it drops to 4%. So this is mostly a wording problem, and it is cheap to fix.

## Slide 3: Failure 2, over-refusing (30 s)
**One line:** The bigger mistake is refusing what is allowed, and a stricter rule makes it worse.

The mistake everyone expects, treating a one-way rule as two-way, happens only 2% of the time. The larger problem is the opposite. In quick answers, models refuse 18% of requests that are plainly on the list. And the sentence that fixed chaining pushes this up to 26%. A test that only counts wrongly allowed requests would call that an improvement.

## Slide 4: Failure 3, no self-knowledge (30 s)
**One line:** Models cannot tell when they are wrong.

We asked every model how confident it was. 97% of the time the answer was exactly 100, whether it was right or wrong. Then we asked them to double-check. One model kept all 740 of its wrong answers. Another changed most of its wrong answers, but also changed 1,194 of its right ones. A rubber stamp or a coin flip, and neither is a safety net.

## Slide 5: What to do (30 s)
**One line:** Three cheap checks before you trust, or explain, a score.

One: split the score, so each kind of mistake has its own request and one explanation. Two: fix the wording, re-run, and watch both wrong allows and wrong refusals. Three: record the model's confidence, but do not rely on it. In 3,319 of 3,579 wrong decisions, the model had every individual step right. The failure is in putting the steps together, and one score cannot show that.
