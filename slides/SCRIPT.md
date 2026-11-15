# Open-Book Epistemics: speaker script

Five slides, about 3 minutes. One line per slide, then what to say.

## Slide 1: The question (35 s)
**One line:** When you tell a model it is wrong, does it check, or agree?

A good answer to "you're wrong" depends on who is right. We already know models give way under pushback, and recent work by Basta and colleagues scores both directions: giving way to a correct objection and to a mistaken one. But in those studies the truth of the objection lives outside the conversation, in medicine or trivia, so the model has nothing to check, and that paper says so in its limitations. I use an open-book task: permission rules, where the answer can be read off a four-line list in the prompt. That lets me make the objection itself a statement about the list, true or false by construction, in the same words both ways. Nine models; the rulebooks are invented and short, so everything is for this task.

## Slide 2: Result 1, checkable pushback (40 s)
**One line:** Six of eight models gave up most right answers to a false claim they could check; two held.

I told models "That is wrong, the list does not include that line" when it does. Six of eight gave up between 57 and 99% of their right answers, with the list still in front of them. Every model accepted the same claim when it was true, so for several of them the response said little about whether the claim was right. Gemini 2.5 Flash and Claude Haiku mostly held. Two cautions: I used one wording, and most replies were one word. A recent paper finds well-known facts are almost never conceded by current models answering in free text, and I cannot yet say which difference explains the gap.

## Slide 3: Result 2, the rule a model cites (35 s)
**One line:** Asked for the rule behind a wrong refusal, two models quoted the rule that permits the request.

After each decision I asked the model to quote the one line that decides the request, or say NONE, and matched the quote against the list by rule. When the decision was right, quote and decision almost always agreed. But after wrongly refusing a listed request, DeepSeek quoted the permitting line in 67 of 79 cases and Llama in 47 of 70. So the decision and the evidence given for it contradict each other, and a simple comparison would catch it. Three other models answered NONE, consistent with their refusal. I did not find this comparison in prior work.

## Slide 4: Replications (30 s)
**One line:** Stated confidence, penalties and tool calls behaved here as prior work reports.

On the same items I repeated several known measurements, and I present them as replications. Stated confidence was exactly 100 in 97% of answers; answer-word probabilities separated right from wrong at 0.78 to 0.87 in the three models where I could read them. A stated penalty for wrong answers rarely produced UNSURE, as several papers have already found. And one model, Grok 4.3, often wrote DECLINE beside a tool call, as reported for harmful requests. The one new variant: stating the Brier rule did not change confidence either.

## Slide 5: From findings to a harness feature (40 s)
**One line:** What works: the harness checks the correction itself. Then most models hold.

So what should a builder do? I tested two fixes on the same false claim. First, the harness checks the claim against the list, which is a string match, and attaches a line saying what it found. Right answers given up fall below 10% in six of eight models; Qwen goes from 99% to zero. Two models, Llama and Nova Lite, still give way, so for those the harness has to hold the decision itself. Second, asking the model to do the check: that helps less, and under pushback five models often report a listed line as missing. From this and the earlier results I propose six guidelines for agent harnesses: check corrections outside the model; do not rely on the model to check; compare what it cites with what it decides, which flagged every wrong allow in stored answers; look up then decide; gate on probabilities, not stated confidence; and enforce on the tool call. The paper ends with a mock-up of a harness layer that applies them. It is a design, not a built product, tested on short rule lists with one wording. The accuracy-score results are in the paper. The test and every raw answer are released.
