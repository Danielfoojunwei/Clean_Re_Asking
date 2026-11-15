"""Run an open-weight model on the benchmark's direct-decision (E1) and lookup (E7) items.
Saves, per item: next-token logits for the two answer words and last-token residual activations at every layer."""
import argparse, json, sys, time
from pathlib import Path
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--gen", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--rounds", default="0-11"); ap.add_argument("--exps", default="E1,E7"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--dtype", default="auto"); ap.add_argument("--device", default="auto")
a = ap.parse_args()
sys.path.insert(0, a.gen)
import gen

torch.set_num_threads(4); torch.manual_seed(0)
tok = AutoTokenizer.from_pretrained(a.model)
DEV = a.device if a.device != "auto" else ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
DT = a.dtype if a.dtype != "auto" else ("float32" if DEV == "cpu" else "float16")
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=getattr(torch, DT)).to(DEV); model.eval()
print("device", DEV, DT, flush=True)
lo, _, hi = a.rounds.partition("-")
EXPS = tuple(a.exps.split(","))
WORDS = {"E1": ("EXECUTE", "DECLINE"), "E7": ("YES", "NO")}
first = {w: tok.encode(w, add_special_tokens=False)[0] for ws in WORDS.values() for w in ws}
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
for rnd in range(int(lo), int(hi or lo) + 1):  # one shard per round, so a stopped run resumes where it left off
  tag = f"r{rnd}_{'-'.join(EXPS)}"
  if (out / f"meta_{tag}.json").exists():
    continue
  items = [it for it in gen.items(rnd) if it["exp"] in EXPS]
  if a.limit:
    items = items[:a.limit]
  meta, acts = [], []
  with torch.no_grad():
    for n, it in enumerate(items):
          ids = tok.apply_chat_template(it["messages"], add_generation_prompt=True, return_tensors="pt")
          ids = (ids["input_ids"] if not torch.is_tensor(ids) else ids).to(DEV)
          o = model(ids, output_hidden_states=True)
          lg = o.logits[0, -1].float()
          w1, w2 = WORDS[it["exp"]]
          lp = torch.log_softmax(lg, -1)
          rec = {k: v for k, v in it.items() if k != "messages"}
          rec.update(logit=[lg[first[w1]].item(), lg[first[w2]].item()], logp=[lp[first[w1]].item(), lp[first[w2]].item()],
                     top=tok.decode(int(lg.argmax())), ntok=int(ids.shape[1]))
          meta.append(rec)
          acts.append(torch.stack([h[0, -1] for h in o.hidden_states]).float().cpu().numpy().astype(np.float16))
          if n % 100 == 0:
              print(rnd, n, len(items), round(time.time() - t0), flush=True)
  np.save(out / f"acts_{tag}.npy", np.stack(acts)); json.dump(meta, open(out / f"meta_{tag}.json", "w"))
  print("round done", rnd, round(time.time() - t0), flush=True)
print("done")
