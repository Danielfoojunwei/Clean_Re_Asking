"""Budget-capped, resumable runner for the epistemic battery (D1-D6)."""
import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v3"))
import gen_d, run, run_c  # noqa: E402  (run_c.call is the frozen request function)

LOCK = threading.Lock()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--rounds", required=True); ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--out", default="runs_d"); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--exps", default="D1,D2,D3,D4,D5,D6")
    a = ap.parse_args()
    lo, _, hi = a.rounds.partition("-")
    sup = run.CATALOG[a.model].get("supported_parameters") or []
    out = Path(a.out) / a.model.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    log, done, spend = out / "responses.jsonl", {}, [0.0]
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line); spend[0] += r.get("cost") or 0.0
            if r["status"] == "ok":
                done[r["id"]] = r
    prior = {}  # the one-line doubt already answered in the earlier pushback run
    p = Path(__file__).resolve().parent.parent / "v3" / "runs_c" / a.model.replace("/", "__") / "responses.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r["status"] == "ok" and r["id"].endswith("/X2-doubt") and r.get("answer"):
                prior[r["id"][:-len("/X2-doubt")]] = r["answer"]
    exps = set(a.exps.split(","))
    todo = [i for r in range(int(lo), int(hi or lo) + 1) for i in gen_d.items(r, a.model, prior) if i["exp"] in exps]
    if a.limit:
        todo = todo[:a.limit]

    def do(item):
        rec = done.get(item["id"])
        if rec is None:
            if item["exp"] == "D4" and item.get("prior"):
                rec = {k: v for k, v in item.items() if k not in ("messages", "one")}
                rec.update(status="ok", content=item["prior"], answer=item["prior"], cost=0.0, reused="X2-doubt")
            else:
                if spend[0] >= a.cap:
                    return
                res = run_c.call(a.model, item, spend, sup)
                rec = {k: v for k, v in item.items() if k not in ("messages", "one")}; rec.update(res)
                if res["status"] == "ok":
                    rec["answer"] = gen_d.score(item, res["content"])
            with LOCK, log.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        if item["exp"] == "D4" and rec.get("status") == "ok":
            nxt = gen_d.next_turn(item, rec.get("answer"))
            if nxt:
                do(nxt)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do, todo))
    print(f"{a.model}: {len(todo)} scheduled, spend so far ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)


if __name__ == "__main__":
    main()
