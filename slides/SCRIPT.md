# One Score, Three Failures: speaker script

Five slides, about 2 minutes 45 seconds. One line per slide, then what to say.

## Slide 1: The problem (30 s)
**One line:** One accuracy score on permission rules hides three different failures.

Here is a rulebook: Finance may send records to Legal, Legal to Audit, and so on. Only the listed directions are allowed. We normally test an AI on rules like this and report one score. We ran the test in three stages across nine models, and wrote down each stage's plan and predictions before its data existed. Stage 1 asked what goes wrong and found three separate failures. Stages 2 and 3 asked why.

## Slide 2: Failure 1, chaining (35 s)
**One line:** Models join rules into chains unless told not to.

Finance may send to Legal, and Legal may send to Audit, so many models conclude Finance may send to Audit. Reasoning step by step, they wrongly allow 44% of these requests. One sentence forbidding chaining brings that to 4%. Why does it happen? Partly the word "route": replace it with "entry" and chaining drops, but two models still chain 64% and 38% of the time. And it grows with the rulebook: the longer the list, the more they chain.

## Slide 3: Failure 2, over-refusing (35 s)
**One line:** Stricter wording makes models refuse what is allowed; stating the rule first fixes it.

The mistake everyone expects, treating a one-way rule as two-way, happens 2% of the time. The bigger problem is the opposite: in quick answers models refuse 18% of requests that are plainly listed, and the stricter sentence pushes that to 26%. We predicted a balanced sentence would repair it. It did not. What worked was structure: ask the model "is the rule listed?" first, then ask for the decision, and refusals fall to a few percent.

## Slide 4: Failure 3, self-report (35 s)
**One line:** Models carry a signal that they are wrong, and do not report it.

Ask a model how sure it is and 97% of the time it says exactly 100, right or wrong. That number is no better than a coin flip at spotting errors. But the probabilities the model puts on its two answer words are informative: they separate right from wrong at 0.78 to 0.87. So the signal is there; the model just does not say it. And asking again does not help: tell it "I think that is wrong" and it drops a third of its correct answers.

## Slide 5: Acting, and what to do (30 s)
**One line:** Score the action, not the words: one model wrote DECLINE and acted anyway.

When we gave models a tool instead of asking for a word, Grok 4.3 carried out 65% of requests that had no supporting rule at all, and in most of those calls its text said DECLINE. So four cheap checks: split the score; re-run with a clearer rule and count wrong refusals too; read answer probabilities instead of asking for confidence; and score the action, not the text. Seven of our thirteen follow-up predictions held, and we report the six that did not.
