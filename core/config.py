"""Repo paths and config loading (configs/pins.json, configs/run_defaults.json)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS = REPO_ROOT / "configs"


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_pins(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or CONFIGS / "pins.json")


def load_run_defaults(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or CONFIGS / "run_defaults.json")


def canonical_json(obj: Any) -> str:
    """Stable JSON used for every hash in the project (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(obj: Any) -> str:
    data = obj if isinstance(obj, (bytes, str)) else canonical_json(obj)
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    """Write via a temp file in the same folder, then rename (no half-written files)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    tmp.replace(path)
