"""The ONE dev/test split (Rule G): made once, stratified by episode type, saved, never remade."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from core.config import REPO_ROOT, atomic_write_text
from core.labels import labels_sha256
from core.schema import Label, Split

SPLIT_PATH = REPO_ROOT / "data" / "split.json"


def compute_split(labels: list[Label], seed: int, dev_frac: float = 0.5) -> tuple[list[str], list[str]]:
    """Per type: sort ids, shuffle with a seeded generator, first round(n*dev_frac) go to dev."""
    by_type: dict[int, list[str]] = defaultdict(list)
    for lb in labels:
        by_type[lb.episode_type].append(lb.game_id)
    rng = np.random.default_rng(seed)
    dev, test = [], []
    for t in sorted(by_type):
        ids = sorted(by_type[t])
        order = rng.permutation(len(ids))
        n_dev = int(np.floor(len(ids) * dev_frac + 0.5))
        dev += [ids[i] for i in order[:n_dev]]
        test += [ids[i] for i in order[n_dev:]]
    return sorted(dev), sorted(test)


def make_split(labels: list[Label], seed: int, dev_frac: float = 0.5, path: Path = SPLIT_PATH) -> Split:
    if path.exists():
        raise FileExistsError(f"{path} already exists; the split is made once and never remade")
    if len({lb.game_id for lb in labels}) != len(labels):
        raise ValueError("duplicate game_id in labels")
    dev, test = compute_split(labels, seed, dev_frac)
    split = Split(created_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), seed=seed,
                  dev_frac=dev_frac, stratify="episode_type", labels_sha256=labels_sha256(labels), dev=dev, test=test)
    atomic_write_text(path, json.dumps(split.to_dict(), indent=1))
    return split


def load_split(path: Path = SPLIT_PATH) -> Split:
    with open(path, encoding="utf-8") as f:
        return Split.from_dict(json.load(f))
