"""Local model access for study L: loading, prompt segmentation, cached-prefix forward passes and residual-stream hooks.

Plain Hugging Face transformers; no API. The residual stream after block L is `hidden_states[L + 1]`
(`hidden_states[0]` is the embedding output). "Layer L" in this study always means the output of block L, L = 0..N-1.
"""
import copy, os, sys
from pathlib import Path
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "study"))
MODEL_DIR = os.environ.get("STUDY_L_MODEL", "/root/models/ministral3b")
MODEL_ID = "mistralai/Ministral-3-3B-Instruct-2512-BF16"
OUT = Path(os.environ.get("STUDY_L_OUT", HERE / "runs"))  # small, committed outputs
BIG = Path(os.environ.get("STUDY_L_BIG", "/root/work/study_l"))  # activations, not committed
torch.set_grad_enabled(False)
torch.set_num_threads(int(os.environ.get("STUDY_L_THREADS", os.cpu_count() or 4)))


class LM:
    def __init__(self):
        from transformers import AutoTokenizer, AutoModelForImageTextToText
        self.tok = AutoTokenizer.from_pretrained(MODEL_DIR, fix_mistral_regex=True)
        full = AutoModelForImageTextToText.from_pretrained(MODEL_DIR, dtype=torch.bfloat16).eval()
        self.full = full
        self.lm = full.model.language_model          # decoder stack
        self.head = full.lm_head
        self.layers = self.lm.layers
        self.n_layers = len(self.layers)
        self.YES, self.NO = (self.tok(w, add_special_tokens=False).input_ids for w in ("YES", "NO"))
        assert len(self.YES) == 1 and len(self.NO) == 1, "YES/NO must be single tokens"
        self.YES, self.NO = self.YES[0], self.NO[0]
        self.normf = copy.deepcopy(self.lm.norm).float()   # final norm and unembedding in float32: bf16 logits are too coarse
        self.Wf = self.head.weight.detach().float()
        self.wd = self.Wf[self.YES] - self.Wf[self.NO]
        self.INST = self.tok.convert_tokens_to_ids("[INST]")
        self.PAD = self.tok.convert_tokens_to_ids("<pad>")
        self._hooks = []

    # ---------- prompts ----------
    def render(self, messages):
        return self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def encode(self, messages, spans=None):
        """Token ids of a rendered conversation, and for each name in `spans` (name -> substring) the token index range
        [a, b) of its last occurrence. Tokens straddling a span boundary count as inside."""
        s = self.render(messages)
        enc = self.tok(s, add_special_tokens=False, return_offsets_mapping=True)
        ids, off = enc.input_ids, enc.offset_mapping
        out = {}
        for name, sub in (spans or {}).items():
            c0 = s.rfind(sub)
            assert c0 >= 0, (name, sub)
            c1 = c0 + len(sub)
            idx = [i for i, (a, b) in enumerate(off) if b > c0 and a < c1 and b > a]
            out[name] = (idx[0], idx[-1] + 1)
        return ids, out

    def split(self, ids):
        """Split at the last [INST]: prefix (shared by all rebuttals of an item) and suffix (the last user turn)."""
        k = len(ids) - 1 - ids[::-1].index(self.INST)
        return ids[:k + 1], ids[k + 1:]

    # ---------- forward ----------
    def logits_of(self, h):
        """Logit lens: final norm and unembedding applied to a residual-stream vector (any layer)."""
        return self.normf(h.float()) @ self.Wf.T

    def ld_of(self, h):
        """YES-minus-NO logit difference read from residual-stream vectors [..., D] (logit lens), in float32."""
        return self.normf(h.float()) @ self.wd

    def prefix_cache(self, prefix_ids):
        out = self.lm(input_ids=torch.tensor([prefix_ids]), use_cache=True)
        return out.past_key_values

    def run(self, suffixes, cache=None, hidden=False, attn_mask=None):
        """Forward a batch of token-id lists (right-padded; causal attention makes padding harmless for earlier positions).
        With `cache` (from prefix_cache) the lists are suffixes continuing that prefix. Returns (last-position logits [B, V],
        hidden states [B, L+1, T, D] or None, lengths)."""
        B = len(suffixes); lens = [len(x) for x in suffixes]; T = max(lens)
        ids = torch.full((B, T), self.PAD, dtype=torch.long)
        for i, x in enumerate(suffixes):
            ids[i, :len(x)] = torch.tensor(x)
        kw = {}
        if cache is not None:
            c = copy.deepcopy(cache)
            if B > 1:
                c.batch_repeat_interleave(B)
            kw["past_key_values"] = c
        if attn_mask is not None:
            kw["attention_mask"] = attn_mask
        out = self.lm(input_ids=ids, use_cache=cache is not None, output_hidden_states=hidden, **kw)
        last = out.last_hidden_state[torch.arange(B), torch.tensor(lens) - 1]
        logits = self.logits_of(last)
        hs = torch.stack(out.hidden_states, 1) if hidden else None
        return logits, hs, lens

    def generate(self, ids, max_new=8, temperature=0.0, n=1, seed=0, cache=None):
        """Greedy (temperature 0) or sampled continuation of one prompt, n samples. Returns list of strings and the
        first-step logits. `ids` continues `cache` when given."""
        g = torch.Generator().manual_seed(seed)
        c = copy.deepcopy(cache) if cache is not None else None
        if c is not None and n > 1:
            c.batch_repeat_interleave(n)
        cur = torch.tensor([ids]).repeat(n, 1)
        done = torch.zeros(n, dtype=torch.bool); outs = [[] for _ in range(n)]; first = None
        eos = self.tok.eos_token_id
        for step in range(max_new):
            o = self.lm(input_ids=cur, past_key_values=c, use_cache=True)
            c = o.past_key_values
            lg = self.logits_of(o.last_hidden_state[:, -1])
            if first is None:
                first = lg[0].clone()
            nxt = lg.argmax(-1) if temperature == 0 else torch.multinomial(torch.softmax(lg / temperature, -1), 1, generator=g)[:, 0]
            for i in range(n):
                if not done[i]:
                    if nxt[i].item() == eos:
                        done[i] = True
                    else:
                        outs[i].append(nxt[i].item())
            if done.all():
                break
            cur = nxt[:, None]
        return [self.tok.decode(x, skip_special_tokens=True) for x in outs], first

    # ---------- hooks on the residual stream ----------
    def clear(self):
        for h in self._hooks:
            h.remove()
        self._hooks = []

    def hook_layer(self, layer, fn):
        """fn(resid [B, T, D]) -> resid, applied to the output of block `layer`."""
        def f(mod, args, out):
            if isinstance(out, tuple):
                return (fn(out[0]),) + tuple(out[1:])
            return fn(out)
        self._hooks.append(self.layers[layer].register_forward_hook(f))


def answer_stats(lm, logits, gold):
    """From last-position logits: the full-vocabulary argmax word, YES-minus-NO logit difference, the logit difference
    signed towards `gold`, the two-way probability of gold and the two-way entropy in bits."""
    y, n = logits[lm.YES].item(), logits[lm.NO].item()
    top = lm.tok.decode([logits.argmax().item()]).strip()
    ans = top.upper() if top.upper() in ("YES", "NO") else None
    d = y - n
    p_yes = 1 / (1 + pow(2.718281828459045, -d))
    p_gold = p_yes if gold == "YES" else 1 - p_yes
    import math
    ent = 0.0 if p_yes in (0.0, 1.0) else -(p_yes * math.log2(p_yes) + (1 - p_yes) * math.log2(1 - p_yes))
    pv = torch.softmax(logits, -1)
    return dict(answer=ans, top=top, ld_yes=round(d, 4), ld_gold=round(d if gold == "YES" else -d, 4), p_gold=round(p_gold, 5),
                entropy=round(ent, 5), mass=round((pv[lm.YES] + pv[lm.NO]).item(), 5))
