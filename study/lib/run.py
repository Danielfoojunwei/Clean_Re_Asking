"""Budget-capped, resumable runner for V2. One process per model. Complete rounds only."""
import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import gen

API = "https://openrouter.ai/api/v1/chat/completions"
LOCK = threading.Lock()
CATALOG = {m["id"]: m for m in json.load(open(Path(__file__).with_name("models.json")))["data"]}


def norm(text):
    t = (text or "").strip()
    return t[:-1].strip() if t.endswith(".") else t


def parse(exp, text):
    """Return the scored answer or None (malformed). Rules are fixed in PLAN.md."""
    t = norm(text)
    if exp in ("E0", "E1"):
        return t if t in ("EXECUTE", "DECLINE") else None
    if exp == "E3":
        return t if t in ("KEEP", "CHANGE") else None
    if exp == "E7":
        return t if t in ("YES", "NO") else None
    if exp == "E6":
        return t if re.fullmatch(r"[A-Za-z]+", t) else None
    if exp == "E2":
        m = re.fullmatch(r"(\d{1,3})%?", t)
        return int(m.group(1)) if m and 0 <= int(m.group(1)) <= 100 else None
    lines = [norm(x) for x in (text or "").splitlines() if x.strip()]
    if not lines:
        return None
    if exp in ("E4", "E4p"):
        return lines[-1] if lines[-1] in ("EXECUTE", "DECLINE") else None
    if exp == "E5":
        m = re.search(r"FINAL:\s*(EXECUTE|DECLINE)$", lines[-1])
        return m.group(1) if m else None
    raise ValueError(exp)


def call(model, item, spend, reasoning_off):
    payload = {"model": model, "messages": item["messages"], "temperature": 0, "max_tokens": item["max_tokens"],
               "stream": False}
    if reasoning_off:
        payload["reasoning"] = {"enabled": False}
    body = json.dumps(payload).encode()
    last = None
    for attempt in range(7):
        req = Request(API, data=body, headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                                               "Content-Type": "application/json",
                                               "X-OpenRouter-Title": "one-way permission benchmark"})
        t0 = time.time()
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
                    p = CATALOG[model]["pricing"]
                    cost = (usage.get("prompt_tokens", 0) * float(p["prompt"]) +
                            usage.get("completion_tokens", 0) * float(p["completion"]))
                with LOCK:
                    spend[0] += float(cost)
                return {"status": "ok", "content": (ch.get("message") or {}).get("content"),
                        "finish": ch.get("finish_reason"), "provider": data.get("provider"),
                        "model_served": data.get("model"), "cost": float(cost), "attempts": attempt + 1,
                        "tokens": [usage.get("prompt_tokens"), usage.get("completion_tokens")],
                        "elapsed": round(time.time() - t0, 2), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except HTTPError as e:
            detail = e.read()[:200].decode("utf-8", "replace")
            last = {"status": "http_error", "code": e.code, "detail": detail}
            if e.code in (400, 401, 402, 403, 404):
                break
        except (URLError, TimeoutError, OSError, ValueError) as e:
            last = {"status": "transport_error", "detail": str(e)[:200]}
        time.sleep(min(60, 2 ** attempt + 0.5))
    last["attempts"] = attempt + 1
    last["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rounds", required=True, help="e.g. 0 or 1-8")
    ap.add_argument("--cap", type=float, required=True, help="hard USD cap for this model, all rounds")
    ap.add_argument("--round-cost", type=float, default=0.0, help="expected USD per round; a round starts only if it fits")
    ap.add_argument("--out", default="runs")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--reasoning-off", type=int, default=-1)
    a = ap.parse_args()
    lo, _, hi = a.rounds.partition("-")
    rounds = range(int(lo), int(hi or lo) + 1)
    out = Path(a.out) / a.model.replace("/", "__")
    out.mkdir(parents=True, exist_ok=True)
    log = out / "responses.jsonl"
    done, spend = {}, [0.0]
    if log.exists():
        for line in log.read_text().splitlines():
            r = json.loads(line)
            spend[0] += r.get("cost") or 0.0
            if r["status"] == "ok":
                done[r["id"]] = r
    roff = a.reasoning_off if a.reasoning_off >= 0 else int(
        "reasoning" in (CATALOG[a.model].get("supported_parameters") or []))

    def do(item):
        if item["id"] in done:
            return
        if spend[0] >= a.cap:
            return
        res = call(a.model, item, spend, roff)
        rec = {k: v for k, v in item.items() if k != "messages"}
        rec.update(res)
        if res["status"] == "ok":
            rec["answer"] = parse(item["exp"], res["content"])
        with LOCK:
            with log.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            if res["status"] == "ok":
                done[item["id"]] = rec

    for rnd in rounds:
        if spend[0] + a.round_cost > a.cap:
            print(f"{a.model}: round {rnd} not started (spend {spend[0]:.3f} + {a.round_cost:.3f} > cap {a.cap})", flush=True)
            break
        first = gen.items(rnd)
        with ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(do, first))
        second = []
        for it in first:
            if it["exp"] == "E1" and it["id"] in done and done[it["id"]].get("answer"):
                second += gen.followups(it, done[it["id"]]["answer"])
        with ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(do, second))
        ids = [i["id"] for i in first + second]
        got = sum(i in done for i in ids)
        (out / f"round{rnd}.status.json").write_text(json.dumps(
            {"round": rnd, "expected": len(ids), "ok": got, "spend_total": round(spend[0], 5),
             "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))
        print(f"{a.model}: round {rnd} {got}/{len(ids)} ok, spend {spend[0]:.4f}", flush=True)


if __name__ == "__main__":
    main()
