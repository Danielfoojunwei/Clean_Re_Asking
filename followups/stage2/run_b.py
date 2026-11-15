"""Budget-capped, resumable runner for the follow-up. Requests token log-probabilities where the model supports them."""
import argparse, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
import gen_b, run  # noqa: E402  (run.parse and the model catalog come from the frozen runner)

LOCK = threading.Lock()
ONLY = []  # optional provider pin for token-probability calls


def call(model, item, spend, reasoning_off, logprobs):
    payload = {"model": model, "messages": item["messages"], "temperature": 0, "max_tokens": item["max_tokens"], "stream": False}
    if reasoning_off:
        payload["reasoning"] = {"enabled": False}
    if logprobs and item["exp"] == "E1":
        payload.update(logprobs=True, top_logprobs=5, provider={"require_parameters": True})
        if ONLY:
            payload["provider"] = {"only": ONLY, "allow_fallbacks": False}
    body, last = json.dumps(payload).encode(), None
    for attempt in range(7):
        req = Request(run.API, data=body, headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                                                   "Content-Type": "application/json", "X-OpenRouter-Title": "one-way permission benchmark"})
        try:
            with urlopen(req, timeout=90) as r:
                data = json.load(r)
            if data.get("error"):
                last = {"status": "provider_error", "detail": str(data["error"])[:200]}
            else:
                ch = (data.get("choices") or [{}])[0]
                usage = data.get("usage") or {}
                cost = usage.get("cost")
                if cost is None:
                    p = run.CATALOG[model]["pricing"]
                    cost = usage.get("prompt_tokens", 0) * float(p["prompt"]) + usage.get("completion_tokens", 0) * float(p["completion"])
                with LOCK:
                    spend[0] += float(cost)
                lp = ((ch.get("logprobs") or {}).get("content") or [])
                first = [[t["token"], round(t["logprob"], 4)] for t in lp[0].get("top_logprobs", [])] if lp else None
                return {"status": "ok", "content": (ch.get("message") or {}).get("content"), "finish": ch.get("finish_reason"),
                        "provider": data.get("provider"), "model_served": data.get("model"), "cost": float(cost),
                        "first_token": [lp[0]["token"], round(lp[0]["logprob"], 4)] if lp else None, "top": first,
                        "attempts": attempt + 1, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except HTTPError as e:
            last = {"status": "http_error", "code": e.code, "detail": e.read()[:200].decode("utf-8", "replace")}
            if e.code in (400, 401, 402, 403, 404):
                break
        except (URLError, TimeoutError, OSError, ValueError) as e:
            last = {"status": "transport_error", "detail": str(e)[:200]}
        time.sleep(min(60, 2 ** attempt + 0.5))
    last.update(attempts=attempt + 1, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--rounds", required=True); ap.add_argument("--conds", required=True)
    ap.add_argument("--exps", default="E1"); ap.add_argument("--cap", type=float, required=True); ap.add_argument("--out", default="runs_b")
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default=""); ap.add_argument("--no-logprobs", action="store_true")
    a = ap.parse_args()
    ONLY.extend(x for x in a.only.split(",") if x)
    lo, _, hi = a.rounds.partition("-")
    sup = run.CATALOG[a.model].get("supported_parameters") or []
    out = Path(a.out) / a.model.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    log, done, spend = out / "responses.jsonl", set(), [0.0]
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line); spend[0] += r.get("cost") or 0.0
            if r["status"] == "ok":
                done.add(r["id"])
    todo = [i for r in range(int(lo), int(hi or lo) + 1) for c in a.conds.split(",") for i in gen_b.items(r, c, tuple(a.exps.split(",")))]
    todo = [i for i in todo if i["id"] not in done]
    if a.limit:
        todo = todo[:a.limit]

    def do(item):
        if spend[0] >= a.cap:
            return
        res = call(a.model, item, spend, "reasoning" in sup, "logprobs" in sup and not a.no_logprobs)
        rec = {k: v for k, v in item.items() if k != "messages"}; rec.update(res)
        if res["status"] == "ok":
            rec["answer"] = run.parse(item["exp"], res["content"])
        with LOCK, log.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do, todo))
    print(f"{a.model}: {len(todo)} scheduled, spend so far ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)


if __name__ == "__main__":
    main()
