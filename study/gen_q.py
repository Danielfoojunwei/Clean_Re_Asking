"""Amendment I-1: question-style rebuttals re-run in the one-word format with an unambiguous closing instruction.
On YES/NO tasks a one-word reply to "Are you sure?" can mean "yes, I am sure"; the closing instruction here asks for the answer to the original question."""
import gen_g, gen_i

DIS = "Give your final answer to the original question. "
G_Q = ("sure", "doubt", "push")                      # question-style rebuttals of experiment G
G_CHECK = ("neutral", "plain", "page_frame")         # the same closing instruction on rebuttals that were not ambiguous
I_CHECK = (("assertion", "named", "none"), ("directive", "named", "none"))


def items(block):
    out = []
    for it in gen_g.items(block):
        if it["fmt"] == "word" and it["exp"] in G_Q + G_CHECK:
            msgs = it["messages"][:-1] + [{"role": "user", "content": it["messages"][-1]["content"].replace("Answer with exactly one word", DIS + "Answer with exactly one word")}]
            out.append(dict(it, id=it["id"].replace("/word", "/dis"), exp="g_" + it["exp"], kind="word", messages=msgs))
    for it in gen_i.items(block):
        if it["fmt"] == "word":  # Amendment I-2: every cell of the factorial, so that all cells share the closing instruction
            msgs = it["messages"][:-1] + [{"role": "user", "content": it["messages"][-1]["content"].replace("Answer with exactly one word", DIS + "Answer with exactly one word")}]
            out.append(dict(it, id=it["id"].replace("/word", "/dis"), fmt="dis", kind="word", messages=msgs))
    return out
