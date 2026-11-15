"""Runner for experiment H. Usage: python3 run_h.py --model M --cap 2.0 [--long] [--blocks 0-3]"""
import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import gen_g, gen_h, gen_i, run, run_c  # noqa: E402

LOCK = threading.Lock()
ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--cap", type=float, required=True); ap.add_argument("--long", action="store_true")
ap.add_argument("--workers", type=int, default=8); ap.add_argument("--blocks", default="0-3"); ap.add_argument("--out", default="runs_h"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--exp", default="h"); ap.add_argument("--fmt", default=""); ap.add_argument("--acts", default="")
a = ap.parse_args()
sup = run.CATALOG[a.model].get("supported_parameters") or []
out = Path(a.out) / a.model.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
log, done, spend = out / "responses.jsonl", {}, [0.0]
if log.exists():
    for line in log.read_text().splitlines():
        r = json.loads(line); spend[0] += r.get("cost") or 0.0
        if r["status"] == "ok":
            done[r["id"]] = r
lo, _, hi = a.blocks.partition("-")
import gen_q
GEN = {'i': gen_i, 'q': gen_q}.get(a.exp, gen_h)
todo = [i for b in range(int(lo), int(hi or lo) + 1) for i in GEN.items(b) if (not a.fmt or i.get('fmt') == a.fmt) and (not a.acts or i.get('act') in a.acts.split(','))]
if a.limit:
    todo = todo[::max(1, len(todo) // a.limit)][:a.limit]
DEC = dict(step="decide")


def ask(item, rid, messages, max_tokens, step):
    """One call (or the stored record). Returns the record, or None if the cap is reached."""
    rec = done.get(rid)
    if rec is None:
        if spend[0] >= a.cap:
            return None
        it = dict(item, messages=messages, max_tokens=150 if (a.long and step == "decide") else max_tokens, step=step)
        res = run_c.call(a.model, it, spend, sup)
        rec = {k: v for k, v in item.items() if k not in ("messages", "one", "turns")}; rec.update(res); rec.update(id=rid, step=step)
        if res["status"] == "ok":
            rec["answer"] = gen_g.score(dict(step=step), res["content"], a.long)
        with LOCK, log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec if rec.get("status") == "ok" else None


def do(item):
    k, msgs = item["kind"], item["messages"]
    if k == "word":
        ask(item, item["id"], msgs, 16, "decide")
    elif k in ("free", "quote"):
        r = ask(item, item["id"], msgs, item["max_tokens"], "reply")
        if r:
            tail = (gen_g.FINAL_FREE if k == "free" else "State your final answer. ") + item["one"]
            ask(item, item["id"] + "-final", msgs + [{"role": "assistant", "content": r["content"] or "(no reply)"}, {"role": "user", "content": tail}], 16, "decide")
    else:  # multi: one-word decisions, stop at the first change of answer
        for t, text in enumerate(item["turns"], 1):
            msgs = msgs + [{"role": "user", "content": text + " " + item["one"]}]
            r = ask(dict(item, turn=t), f'{item["id"]}-t{t}', msgs, 16, "decide")
            if not r or r.get("answer") != item["prior"]:
                break
            msgs = msgs + [{"role": "assistant", "content": r["content"] or item["prior"]}]


with ThreadPoolExecutor(a.workers) as ex:
    list(ex.map(do, todo))
print(f"{a.model}: {len(todo)} scheduled, spend ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)
