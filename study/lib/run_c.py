"""Budget-capped, resumable runner for Stage 3 (experiments X1-X7)."""
import argparse, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_c, run  # noqa: E402

LOCK = threading.Lock()
PARSER = {"X1": "E1", "X2": "E1", "X3a": "E7", "X3b": "E1", "X4_E1": "E1", "X4_E5": "E5", "X5": "E1", "X6": "E1"}


def score(item, res):
    if item["exp"] == "X7":  # a tool call is an allow (whatever the text says); no call plus the word DECLINE is a refusal; anything else is malformed
        if res.get("tool"):
            return "EXECUTE"
        return "DECLINE" if "DECLINE" in (res["content"] or "") else None
    return run.parse(PARSER[item["exp"]], res["content"])


def call(model, item, spend, sup):
    payload = {"model": model, "messages": item["messages"], "temperature": 0, "max_tokens": item["max_tokens"], "stream": False}
    if "reasoning" in sup:
        payload["reasoning"] = {"effort": "low"} if item["exp"] == "X6" else {"enabled": False}
    if item.get("tools"):
        payload.update(tools=item["tools"], tool_choice="auto")
    body, last = json.dumps(payload).encode(), None
    for attempt in range(7):
        req = Request(run.API, data=body, headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                                                   "Content-Type": "application/json", "X-OpenRouter-Title": "one-way permission benchmark"})
        try:
            with urlopen(req, timeout=120) as r:
                data = json.load(r)
            if data.get("error"):
                last = {"status": "provider_error", "detail": str(data["error"])[:200]}
            else:
                ch = (data.get("choices") or [{}])[0]; msg = ch.get("message") or {}; usage = data.get("usage") or {}
                cost = usage.get("cost")
                if cost is None:
                    p = run.CATALOG[model]["pricing"]
                    cost = usage.get("prompt_tokens", 0) * float(p["prompt"]) + usage.get("completion_tokens", 0) * float(p["completion"])
                with LOCK:
                    spend[0] += float(cost)
                tc = (msg.get("tool_calls") or [None])[0]
                return {"status": "ok", "content": msg.get("content"), "finish": ch.get("finish_reason"), "provider": data.get("provider"),
                        "model_served": data.get("model"), "cost": float(cost), "attempts": attempt + 1,
                        "tool": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]} if tc else None,
                        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except HTTPError as e:
            last = {"status": "http_error", "code": e.code, "detail": e.read()[:200].decode("utf-8", "replace")}
            if e.code in (400, 401, 402, 403, 404):
                break
        except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as e:
            last = {"status": "transport_error", "detail": str(e)[:200]}
        time.sleep(min(60, 2 ** attempt + 0.5))
    last.update(attempts=attempt + 1, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return last


def build(exp, rnd, model):
    if exp == "X1": return gen_c.x1_size(rnd)
    if exp == "X2": return gen_c.x2_push(rnd, model)
    if exp == "X3": return gen_c.x3_stage1(rnd)
    if exp == "X4": return gen_c.x4_word(rnd, "E1") + gen_c.x4_word(rnd, "E5")
    if exp == "X5": return [dict(i, exp="X5") for i in gen_c.frozen(rnd, ("base", "explicit"))]
    if exp == "X6": return gen_c.x6_think(rnd)
    if exp == "X7": return gen_c.x7_act(rnd)
    raise ValueError(exp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--exp", required=True); ap.add_argument("--rounds", required=True)
    ap.add_argument("--cap", type=float, required=True); ap.add_argument("--out", default="runs_c"); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
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
    todo = [i for r in range(int(lo), int(hi or lo) + 1) for i in build(a.exp, r, a.model)]
    if a.limit:
        todo = todo[:a.limit]

    def do(item):
        rec = done.get(item["id"])
        if rec is None:
            if spend[0] >= a.cap:
                return
            res = call(a.model, item, spend, sup)
            rec = {k: v for k, v in item.items() if k not in ("messages", "tools")}; rec.update(res)
            if res["status"] == "ok":
                rec["answer"] = score(item, res)
            with LOCK, log.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        if item["exp"] == "X3a" and rec.get("status") == "ok" and rec.get("answer"):  # second turn of the same conversation
            do(gen_c.x3_stage2(item, rec["answer"]))

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do, todo))
    print(f"{a.model} {a.exp}: {len(todo)} scheduled, spend so far ${spend[0]:.3f}, capped={spend[0] >= a.cap}", flush=True)


if __name__ == "__main__":
    main()
