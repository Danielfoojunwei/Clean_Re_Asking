"""Load the per-round shards written by extract.py."""
import json, re
from pathlib import Path
import numpy as np


def load(d, exp="E1"):
    d = Path(d)
    files = sorted(d.glob(f"meta_r*_{exp}.json"), key=lambda p: int(re.search(r"_r(\d+)_", p.name).group(1)))
    meta = [m for f in files for m in json.load(open(f))]
    acts = np.concatenate([np.load(str(f).replace("meta_", "acts_").replace(".json", ".npy")) for f in files]) if files else None
    return meta, acts
