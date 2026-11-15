"""Runner for experiment F. Usage: python3 run_f.py --model M --cap 0.3 [--long]"""
import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2")); sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v3"))
import gen_f, run, run_c  # noqa: E402

LOCK = threading.Lock()
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--cap", type=float, required=True); ap.add_argument("--long", action="store_true"); ap.add_argument("--workers", type=int, default=8)
a = ap.parse_args()
sup = run.CATALOG[a.model].get("supported_parameters") or []
out = Path("runs_f") / a.model.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
log, done, spend = out / "responses.jsonl", {}, [0.0]
if log.exists():
    for line in log.read_text().splitlines():
        r = json.loads(line); spend[0] += r.get("cost") or 0.0
        if r["status"] == "ok":
            done[r["id"]] = r
todo = [i for b in range(gen_f.BLOCKS) for i in gen_f.items(b)]


def do(item):
    if a.long:
        item["max_tokens"] = 150
    rec = done.get(item["id"])
    if rec is None:
        if spend[0] >= a.cap:
            return
        res = run_c.call(a.model, item, spend, sup)
        rec = {k: v for k, v in item.items() if k not in ("messages", "one")}; rec.update(res)
        if res["status"] == "ok":
            rec["answer"] = gen_f.score(item, res["content"], a.long)
        with LOCK, log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    if item["exp"] == "check" and rec.get("status") == "ok":
        do(gen_f.next_turn(item, rec["content"] or ""))


with ThreadPoolExecutor(a.workers) as ex:
    list(ex.map(do, todo))
print(f"{a.model}: {len(todo)} scheduled, spend ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)
