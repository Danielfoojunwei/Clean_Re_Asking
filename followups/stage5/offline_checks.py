"""Two harness checks evaluated on stored responses (no new model calls).
(1) cite-and-compare: flag a decision when the quoted line does not match it (EXECUTE needs the requested line; DECLINE needs NONE).
(2) probability gate: flag a decision when the probability of its first answer token is below 0.90."""
import json, math, glob
from pathlib import Path
HERE = Path(__file__).resolve().parent
LAB = {m: v["label"] for m, v in json.load(open(HERE / "results_d.json"))["models"].items()}
out = {"cite": {}, "gate": {}}
for mid, lab in LAB.items():
    rows = {}
    for line in open(HERE / "runs_d" / mid.replace("/", "__") / "responses.jsonl"):
        r = json.loads(line)
        if r["status"] == "ok" and r["exp"] == "D5":
            rows[r["id"]] = r
    flag = lambda r: not ((r["e1_answer"] == "EXECUTE" and r["answer"] == "supports") or (r["e1_answer"] == "DECLINE" and r["answer"] == "none"))
    wrong = [r for r in rows.values() if r["e1_answer"] != r["gold"]]; right = [r for r in rows.values() if r["e1_answer"] == r["gold"]]
    wa = [r for r in wrong if r["e1_answer"] == "EXECUTE"]; wr = [r for r in wrong if r["e1_answer"] == "DECLINE"]
    out["cite"][lab] = {"wrong_flagged": [sum(map(flag, wrong)), len(wrong)], "wrong_allow_flagged": [sum(map(flag, wa)), len(wa)],
                        "wrong_refusal_flagged": [sum(map(flag, wr)), len(wr)], "right_flagged": [sum(map(flag, right)), len(right)]}
for f in sorted(glob.glob(str(HERE.parent / "v3" / "runs_b" / "*" / "responses.jsonl"))):
    rows = {}
    for line in open(f):
        r = json.loads(line)
        if r["status"] == "ok" and r["exp"] == "E1" and r.get("clause") == "base" and r.get("first_token") and r.get("answer") in ("EXECUTE", "DECLINE"):
            rows[r["id"]] = r
    if not rows:
        continue
    mid = Path(f).parent.name.replace("__", "/")
    lab = LAB.get(mid, mid)
    low = lambda r: math.exp(r["first_token"][1]) < 0.90
    wrong = [r for r in rows.values() if r["answer"] != r["gold"]]; right = [r for r in rows.values() if r["answer"] == r["gold"]]
    out["gate"][lab] = {"wrong_flagged": [sum(map(low, wrong)), len(wrong)], "right_flagged": [sum(map(low, right)), len(right)]}
tot = lambda d, k: [sum(v[k][0] for v in d.values()), sum(v[k][1] for v in d.values())]
out["cite_total"] = {k: tot(out["cite"], k) for k in ("wrong_flagged", "wrong_allow_flagged", "wrong_refusal_flagged", "right_flagged")}
out["gate_total"] = {k: tot(out["gate"], k) for k in ("wrong_flagged", "right_flagged")}
json.dump(out, open(HERE / "results_checks.json", "w"), indent=1)
for k in ("cite", "gate"):
    for l, v in out[k].items():
        print(k, l, v)
print(out["cite_total"], out["gate_total"])
