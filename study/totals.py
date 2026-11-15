"""Counts scored answers, malformed replies and spend over the G, H, I, Q and J runs."""
import json, glob
out = {}
for d in ("runs_g", "runs_h", "runs_i", "runs_q", "runs_j_sample", "runs_j_logprob"):
    n = bad = 0; c = 0.0; models = set()
    for f in glob.glob(d + "/*/responses.jsonl"):
        seen = {}
        for l in open(f):
            r = json.loads(l); c += r.get("cost") or 0
            if r.get("status") == "ok":
                seen[r.get("id", len(seen))] = r
        n += len(seen); models.add(f.split("/")[1])
    out[d] = {"n": n, "spend": round(c, 2), "models": len(models)}
out["total"] = {"n": sum(v["n"] for v in out.values()), "spend": round(sum(v["spend"] for v in out.values()), 2)}
json.dump(out, open("totals.json", "w"), indent=1); print(out)
