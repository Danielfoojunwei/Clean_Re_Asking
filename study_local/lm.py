"""Local model access for study L: loading, prompt segmentation, cached-prefix forward passes and residual-stream hooks.

Plain Hugging Face transformers; no API. The residual stream after block L is `hidden_states[L + 1]`
(`hidden_states[0]` is the embedding output). "Layer L" in this study always means the output of block L, L = 0..N-1.
"""
import copy, os, sys
from pathlib import Path
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "study"))
MODELS = {  # name -> (Hugging Face id, local directory, MLP weights held in 8-bit)
    "ministral3b": ("mistralai/Ministral-3-3B-Instruct-2512-BF16", "/root/models/ministral3b", False),
    "ministral8b": ("mistralai/Ministral-3-8B-Instruct-2512-BF16", "/root/models/ministral8b", True),
}
NAME = os.environ.get("STUDY_L_MODEL", "ministral8b")
MODEL_ID, MODEL_DIR, QUANT = MODELS[NAME]
OUT = HERE / "runs" / NAME                                   # small, committed outputs
BIG = Path(os.environ.get("STUDY_L_BIG", "/root/work/study_l")) / NAME  # activations, not committed
torch.set_grad_enabled(False)
torch.set_num_threads(int(os.environ.get("STUDY_L_THREADS", os.cpu_count() or 4)))
_BUF = {}


class QLinear(torch.nn.Module):
    """A bias-free linear layer whose weight is stored as int8 with one scale per output row and expanded to bf16 for each
    call. Used for the MLP matrices of the 8B model so that it fits in 16 GB of RAM; attention, embeddings and norms stay bf16."""
    def __init__(self, w):
        super().__init__()
        wf = w.float()
        sc = wf.abs().amax(1, keepdim=True).clamp(min=1e-8) / 127
        self.register_buffer("q", torch.round(wf / sc).to(torch.int8))
        self.register_buffer("s", sc.to(torch.bfloat16))

    def forward(self, x):
        W = _BUF.get(self.q.shape)
        if W is None:
            W = _BUF[self.q.shape] = torch.empty(self.q.shape, dtype=torch.bfloat16)
        W.copy_(self.q); W.mul_(self.s)
        return torch.nn.functional.linear(x, W)


def load_decoder(path, quant):
    """Builds the text decoder from the checkpoint shards one tensor at a time (the vision tower is not loaded)."""
    import json
    from accelerate import init_empty_weights
    from accelerate.utils import set_module_tensor_to_device
    from transformers import AutoConfig, AutoModelForCausalLM
    cfg = AutoConfig.from_pretrained(path).text_config
    with init_empty_weights():
        model = AutoModelForCausalLM.from_config(cfg)
    import struct
    wm = json.load(open(Path(path) / "model.safetensors.index.json"))["weight_map"]
    for shard in sorted(set(wm.values())):
        # plain reads with the page cache dropped as we go: memory-mapped loading counts against the container's memory limit
        with open(Path(path) / shard, "rb", buffering=0) as f:
            n = struct.unpack("<Q", f.read(8))[0]
            header = json.loads(f.read(n))
            for key, info in sorted(header.items(), key=lambda kv: kv[1]["data_offsets"][0] if kv[0] != "__metadata__" else -1):
                if not key.startswith("language_model."):
                    continue
                assert info["dtype"] == "BF16", (key, info["dtype"])
                a0, a1 = info["data_offsets"]
                buf = bytearray(a1 - a0)
                f.seek(8 + n + a0); f.readinto(buf)
                os.posix_fadvise(f.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
                t = torch.frombuffer(buf, dtype=torch.bfloat16).reshape(info["shape"])
                name = key[len("language_model."):]
                if quant and ".mlp." in name:
                    parent = model.get_submodule(name.rsplit(".", 2)[0])
                    setattr(parent, name.split(".")[-2], QLinear(t))
                else:
                    set_module_tensor_to_device(model, name, "cpu", value=t, dtype=torch.bfloat16)
                del t, buf
    if "language_model.lm_head.weight" not in wm:
        model.lm_head.weight = model.model.embed_tokens.weight
    return model.eval()


class LM:
    def __init__(self):
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(MODEL_DIR, fix_mistral_regex=True)
        full = load_decoder(MODEL_DIR, QUANT)
        self.lm = full.model                          # decoder stack
        self.W = full.lm_head.weight                  # unembedding, bf16
        self.layers = self.lm.layers
        self.n_layers = len(self.layers)
        self.YES, self.NO = (self.tok(w, add_special_tokens=False).input_ids for w in ("YES", "NO"))
        assert len(self.YES) == 1 and len(self.NO) == 1, "YES/NO must be single tokens"
        self.YES, self.NO = self.YES[0], self.NO[0]
        self.normf = copy.deepcopy(self.lm.norm).float()   # final norm in float32; YES/NO read-out in float32 (bf16 logits are coarse)
        self.wd = self.W[self.YES].float() - self.W[self.NO].float()
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
        """Full-vocabulary logits from residual-stream vectors (final norm in float32, unembedding in bf16): used for the argmax."""
        return (self.normf(h.float()).to(torch.bfloat16) @ self.W.T).float()

    def ld_of(self, h):
        """YES-minus-NO logit difference read from residual-stream vectors [..., D] (logit lens), in float32."""
        return self.normf(h.float()) @ self.wd

    def prefix_cache(self, prefix_ids):
        out = self.lm(input_ids=torch.tensor([prefix_ids]), use_cache=True)
        return out.past_key_values

    def run(self, suffixes, cache=None, hidden=False, attn_mask=None):
        """Forward a batch of token-id lists (right-padded; causal attention makes padding harmless for earlier positions).
        With `cache` (from prefix_cache) the lists are suffixes continuing that prefix. Returns (last-position residual
        stream before the final norm [B, D], hidden states [B, L+1, T, D] or None, lengths)."""
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
        h = self.layers[-1].register_forward_hook(lambda m, i, o: setattr(self, "_last", o[0] if isinstance(o, tuple) else o))
        try:
            out = self.lm(input_ids=ids, use_cache=cache is not None, output_hidden_states=hidden, **kw)
        finally:
            h.remove()
        hs = torch.stack(out.hidden_states, 1) if hidden else None
        return self._last[torch.arange(B), torch.tensor(lens) - 1], hs, lens

    def generate(self, ids, max_new=8, temperature=0.0, n=1, seed=0, cache=None):
        """Greedy (temperature 0) or sampled continuation of one prompt, n samples. Returns the strings and the first-step
        residual stream (pre-norm, sample 0). `ids` continues `cache` when given."""
        g = torch.Generator().manual_seed(seed)
        c = copy.deepcopy(cache) if cache is not None else None
        if c is not None and n > 1:
            c.batch_repeat_interleave(n)
        cur = torch.tensor([ids]).repeat(n, 1)
        done = torch.zeros(n, dtype=torch.bool); outs = [[] for _ in range(n)]; first = None
        eos = self.tok.eos_token_id
        hk = self.layers[-1].register_forward_hook(lambda m, i, o: setattr(self, "_last", o[0] if isinstance(o, tuple) else o))
        try:
            for step in range(max_new):
                o = self.lm(input_ids=cur, past_key_values=c, use_cache=True)
                c = o.past_key_values
                h = self._last[:, -1]
                lg = self.logits_of(h)
                if first is None:
                    first = h[0].clone()
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
        finally:
            hk.remove()
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


def answer_stats(lm, h, gold):
    """From the last-position residual stream (pre-norm): the full-vocabulary argmax word, the YES-minus-NO logit difference,
    the same signed towards `gold`, the two-way probability of gold, the two-way entropy in bits and the probability mass on
    YES and NO together."""
    import math
    logits = lm.logits_of(h)
    top = lm.tok.decode([logits.argmax().item()]).strip()
    ans = top.upper() if top.upper() in ("YES", "NO") else None
    d = lm.ld_of(h).item()
    p_yes = 1 / (1 + math.exp(-d))
    p_gold = p_yes if gold == "YES" else 1 - p_yes
    ent = 0.0 if p_yes <= 0.0 or p_yes >= 1.0 else -(p_yes * math.log2(p_yes) + (1 - p_yes) * math.log2(1 - p_yes))
    pv = torch.softmax(logits, -1)
    return dict(answer=ans, top=top, ld_yes=round(d, 4), ld_gold=round(d if gold == "YES" else -d, 4), p_gold=round(p_gold, 5),
                entropy=round(ent, 5), mass=round((pv[lm.YES] + pv[lm.NO]).item(), 5))
