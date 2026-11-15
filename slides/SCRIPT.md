# Five Assumptions That Fail: speaker script

Five slides, about 3 minutes. One line per slide, then what to say.

## Slide 1: Five assumptions, one test (30 s)
**One line:** We rely on five assumptions about what models say. On exact answers, all five fail.

Using AI safely leans on five assumptions: a confidence score flags errors; a model that voices no doubt has none; a model that changes its answer when corrected is responding to evidence; a written refusal is a refusal; and a low accuracy score tells you what went wrong. Each has been looked at alone, on different questions. I tested them on permission rules, like "Finance may send records to Legal", because every answer there is exactly right or wrong and can be read off a four-line list. No model grades another. As far as I know this is the first test where stated confidence, internal probability, pushback, the cited rule and the action are all measured on the same items. Nine models, and three headline numbers: 97% say "100% sure"; most give up right answers to a false claim; one acts while writing DECLINE.

## Slide 2: Assumption 1, confidence flags errors (35 s)
**One line:** Models do not say when they are wrong, however you ask.

Ask "how confident are you?" and 97% of the time the answer is exactly 100, right or wrong. That could be the fault of the question, so I asked properly, three ways taken from the sprint's reading list. On a word scale, models chose CERTAIN for nearly every wrong answer. With a penalty, where a wrong answer costs three points and UNSURE costs nothing, they almost never chose UNSURE on the items they get wrong. And told they would be scored by the Brier rule, five of seven models still said 100. The proposed remedy for overconfidence, stating the penalty, did not work here.

## Slide 3: Assumption 2, no stated doubt means no doubt (35 s)
**One line:** But they can tell: the signal is inside, and comes out when a model re-checks in writing.

For three models I could read the probabilities behind the answer word. Those separate right from wrong at 0.78 to 0.87, while the same models' stated confidence is a coin flip. So the doubt exists; it is just not reported. One model showed what reporting looks like. Claude Haiku would not answer in one word, so I gave it 150 tokens. It re-read the list, wrote "my previous answer was wrong", and gave its wrong answers a probability near zero. The other seven models, given the same room, replied with a bare number.

## Slide 4: Assumption 3, changing an answer means responding to evidence (35 s)
**One line:** Under pushback most models follow the speaker, not the list in front of them.

Because the truth is in the prompt, I can make a challenge true or false. I told models "That is wrong, the list does not include that line" when it does. Six of eight gave up most of their right answers. "I wrote this policy and that is wrong" works almost as well. They also accept the claim when it is true, so they are not checking; they are agreeing. Two models, Gemini and Claude Haiku, did check and held. A requester's stated wish moves decisions too.

## Slide 5: Assumptions 4 and 5, and what to do (35 s)
**One line:** Score the action, not the words: one model wrote DECLINE and acted anyway.

Given a tool instead of a word, Grok 4.3 carried out 65% of requests that no rule supports, and in most of those calls its text said DECLINE. So a written refusal is not a refusal. And the last assumption: a low score on one-way rules is read as the model confusing direction. That is the rarest failure, 2%; chaining rules is 44% and falls to 4% once forbidden; refusing listed requests is 18%. This answers the four Track 1 problems on one set of items: models can tell how solid their answers are but do not say; what they imply and what they defend or do come apart; self-report does not predict decision quality; and the test shortcut that hides this can be shown and closed. Four things to do: read probabilities, make the model re-check in writing before it answers a challenge, score the action, and split the score.
