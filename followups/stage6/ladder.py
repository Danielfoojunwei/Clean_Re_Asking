"""One table across three open-book tasks: reads the fact, re-reads it correctly when contradicted, keeps a right answer under a false claim."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
V4, PAPER = HERE.parent / "v4", HERE.parent / "paper"
RD = json.load(open(V4 / "results_d.json")); RE_ = json.load(open(V4 / "results_e.json")); RF = json.load(open(HERE / "results_f.json"))
MAIN = {m["label"]: m for m in json.load(open(PAPER / "fig_data.json"))["models"]}
HK = "anthropic/claude-haiku-5.5"
out = {}
for mid, v in RD["models"].items():
    lab = v["label"]
    # permission task: re-read under a FALSE claim (first answer right), from the raw check-then-decide run
    ok = n = 0
    for line in open(V4 / "runs_e" / mid.replace("/", "__") / "responses.jsonl"):
        r = json.loads(line)
        if r["status"] == "ok" and r["exp"] == "E1" and r["step"] == "check" and r["e1_answer"] == r["gold"]:
            n += 1; ok += r.get("answer") == ("LISTED" if r["listed"] else "MISSING")
    e = RE_["models"][mid]
    lk = MAIN[lab]["components"]["lookup"]
    row = {"permission": {"reads": lk[0] / lk[1], "rereads": ok / n, "keeps": 1 - e["base"]["right_changed"]["rate"], "rereads_n": n}}
    f = RF["models"][mid]
    for dom in ("stock", "rooms"):
        row[dom] = {"reads": f[dom]["read"]["rate"], "rereads": f[dom]["check_correct_false_claim"]["rate"], "keeps": 1 - f[dom]["claim"]["right_changed"]["rate"]}
    out[lab] = row
json.dump(out, open(HERE / "results_ladder.json", "w"), indent=1)
for l, r in out.items():
    print(f"{l:18}", " | ".join(f"{t}: " + "/".join(f"{100 * r[t][k]:.0f}" for k in ("reads", "rereads", "keeps")) for t in ("permission", "stock", "rooms")))
