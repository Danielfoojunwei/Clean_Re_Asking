"""Amendments D-1 and D-2: 150-token limit and whole-word scoring.
Usage: python3 long_format.py [model rounds exps cap]   (defaults: Claude Haiku 5.5, rounds 1-4, D1,D2,D3,D4, cap 0.6)"""
import re, sys
import gen_d, run_d

_items, _next = gen_d.items, gen_d.next_turn


def long(i):
    if i:
        i["max_tokens"] = 150
    return i


def score(item, text):
    t = text or ""
    if item["exp"] == "D1":
        n = {int(x) for x in re.findall(r"(?<![\d.])\d{1,3}(?![\d.])", t) if int(x) <= 100}
        return n.pop() if len(n) == 1 else None
    words = ("EXECUTE", "DECLINE", "UNSURE") if item["exp"] == "D2" else ("EXECUTE", "DECLINE")
    hit = {w for w in words if re.search(rf"\b{w}\b", t)}
    return hit.pop() if len(hit) == 1 else None


gen_d.items = lambda *a, **k: [long(i) for i in _items(*a, **k) if not (i["exp"] == "D1" and i["variant"] == "words")]
gen_d.next_turn = lambda *a, **k: long(_next(*a, **k))
gen_d.score = score
A = sys.argv[1:] + ["anthropic/claude-haiku-5.5", "1-4", "D1,D2,D3,D4", "0.6"][len(sys.argv) - 1:]
sys.argv = ["run_d.py", "--model", A[0], "--rounds", A[1], "--cap", A[3], "--out", "runs_d_long", "--exps", A[2]]
run_d.main()
