"""Experiment J: uncertainty readings under pushback. Sampling (several answers per item at temperature 1) and answer-token probabilities.
Usage: python3 run_j.py --model M --mode sample|logprob --cap 1.0 [--samples 8] [--blocks 0-1] [--only Provider]"""
import argparse, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2"))
import gen_g, run  # noqa: E402

LOCK = threading.Lock()
CONDS = ("neutral", "push", "plain", "citation", "page_frame")  # rebuttals of experiment G, one-word format


def items(block):
    out = []
    for it in gen_g.items(block):
        if it["fmt"] != "word" or it["exp"] not in CONDS:
            continue
        out.append(it)
        if it["exp"] == "neutral" and it["prior_right"]:  # the bare question, once per base item
            out.append(dict(it, id=it["id"].rsplit("/", 3)[0] + "/bare", exp="bare", prior=None, prior_right=None, pushed=None, messages=it["messages"][:2]))
    return out


def call(model, messages, max_tokens, temperature, logprobs, only, sup, spend):
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    if "reasoning" in sup:
        payload["reasoning"] = {"enabled": False}
    if logprobs:
        payload.update(logprobs=True, top_logprobs=5, provider={"require_parameters": True})
        if only:
            payload["provider"] = {"only": only, "allow_fallbacks": False}
    body, last = json.dumps(payload).encode(), None
    for attempt in range(6):
        req = Request(run.API, data=body, headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json", "X-OpenRouter-Title": "one-way permission benchmark"})
        try:
            with urlopen(req, timeout=120) as r:
                data = json.load(r)
            if data.get("error"):
                last = {"status": "provider_error", "detail": str(data["error"])[:200]}
            else:
                ch = (data.get("choices") or [{}])[0]; msg = ch.get("message") or {}; usage = data.get("usage") or {}
                cost = usage.get("cost")
                if cost is None:
                    p = run.CATALOG[model]["pricing"]; cost = usage.get("prompt_tokens", 0) * float(p["prompt"]) + usage.get("completion_tokens", 0) * float(p["completion"])
                with LOCK:
                    spend[0] += float(cost)
                lp = ((ch.get("logprobs") or {}).get("content") or [])
                return {"status": "ok", "content": msg.get("content"), "provider": data.get("provider"), "cost": float(cost), "attempts": attempt + 1,
                        "top": [[t["token"], round(t["logprob"], 4)] for t in lp[0].get("top_logprobs", [])] if lp else None,
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except HTTPError as e:
            last = {"status": "http_error", "code": e.code, "detail": e.read()[:200].decode("utf-8", "replace")}
            if e.code in (400, 401, 402, 403, 404):
                break
        except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as e:
            last = {"status": "transport_error", "detail": str(e)[:200]}
        time.sleep(min(60, 2 ** attempt + 0.5))
    last.update(attempts=attempt + 1)
    return last


def word(text):
    hit = {w for w in ("YES", "NO") if re.search(rf"\b{w}\b", (text or "").upper())}
    return hit.pop() if len(hit) == 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--mode", required=True); ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--samples", type=int, default=8); ap.add_argument("--blocks", default="0-1"); ap.add_argument("--only", default=""); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=""); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    sup = run.CATALOG[a.model].get("supported_parameters") or []
    out = Path(a.out or f"runs_j_{a.mode}") / a.model.replace("/", "__"); out.mkdir(parents=True, exist_ok=True)
    log, done, spend = out / "responses.jsonl", set(), [0.0]
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line); spend[0] += r.get("cost") or 0.0
            if r["status"] == "ok":
                done.add(r["id"])
    lo, _, hi = a.blocks.partition("-")
    base = [i for b in range(int(lo), int(hi or lo) + 1) for i in items(b)]
    if a.limit:
        base = base[::max(1, len(base) // a.limit)][:a.limit]
    todo = [(i, k) for i in base for k in (range(a.samples) if a.mode == "sample" else [0])]

    def do(job):
        item, k = job
        rid = f'{item["id"]}#{k}' if a.mode == "sample" else item["id"]
        if rid in done or spend[0] >= a.cap:
            return
        res = call(a.model, item["messages"], 16, 1.0 if a.mode == "sample" else 0, a.mode == "logprob", [x for x in a.only.split(",") if x], sup, spend)
        rec = {k_: v for k_, v in item.items() if k_ != "messages"}; rec.update(res); rec.update(id=rid, sample=k)
        if res["status"] == "ok":
            rec["answer"] = word(res["content"])
        with LOCK, log.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do, todo))
    print(f"{a.model} {a.mode}: {len(todo)} scheduled, spend ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)


if __name__ == "__main__":
    main()
