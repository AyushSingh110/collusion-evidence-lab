"""Ground-truth labels. Rule G: the label comes ONLY from how the game was generated (episode_type)."""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Union

from core.config import REPO_ROOT, atomic_write_text, sha256_of
from core.schema import EPISODE_TYPES, GameConfig, Label

LABELS_PATH = REPO_ROOT / "data" / "labels.csv"
_COLUMNS = ["game_id", "episode_type", "collusion", "focal_pair", "variant", "synthetic"]


def label_from_config(cfg: Union[GameConfig, dict[str, Any]]) -> Label:
    """collusion = 1 for Type 1, else 0. Only episode_type decides it; the other fields are copied for joining."""
    c = cfg.to_dict() if isinstance(cfg, GameConfig) else cfg
    et = c["episode_type"]
    if et not in EPISODE_TYPES:
        raise ValueError(f"episode_type {et!r} not in {EPISODE_TYPES}")
    return Label(game_id=c["game_id"], episode_type=et, collusion=1 if et == 1 else 0,
                 focal_pair=list(c["focal_pair"]), variant=c.get("variant", ""), synthetic=bool(c.get("synthetic", False)))


def labels_csv_text(labels: list[Label]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(_COLUMNS)
    for lb in sorted(labels, key=lambda x: x.game_id):
        w.writerow([lb.game_id, lb.episode_type, lb.collusion, "|".join(lb.focal_pair), lb.variant,
                    str(lb.synthetic).lower()])
    return buf.getvalue()


def labels_sha256(labels: list[Label]) -> str:
    return sha256_of(labels_csv_text(labels))


def write_labels(labels: list[Label], path: Path = LABELS_PATH) -> Path:
    """Write labels.csv. Refuses to replace an existing file with different content (the split depends on it)."""
    text = labels_csv_text(labels)
    if len({lb.game_id for lb in labels}) != len(labels):
        raise ValueError("duplicate game_id in labels")
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise FileExistsError(f"{path} exists with different content; refusing to overwrite")
    atomic_write_text(path, text)
    return path


def read_labels(path: Path = LABELS_PATH) -> list[Label]:
    with open(path, encoding="utf-8", newline="") as f:
        return [Label(game_id=r["game_id"], episode_type=int(r["episode_type"]), collusion=int(r["collusion"]),
                      focal_pair=r["focal_pair"].split("|"), variant=r["variant"], synthetic=r["synthetic"] == "true")
                for r in csv.DictReader(f)]
