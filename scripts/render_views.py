"""Clean GameRecords and render monitor views (report 00 §7, §11).

Run from the repo root:
  conda run -n collusion-lab python scripts/render_views.py --input data/raw --views V1,V2,V3,V4 \
      [--setup-texts setup_texts.json] [--labels data/labels.csv --split data/split.json] [--dry-run]

Writes data/clean/<game_id>.json, data/clean_private/<game_id>.json, data/clean/leak_hits.jsonl (removals),
data/clean/leak_flags.jsonl (flag-only hits, type-blind) and
data/views/<view>/<game_id>.txt + data/views/manifest.json. C-mismatch needs --labels and --split
(type and split of every game); without them it is skipped and listed in the manifest.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clean.cleaner import clean_game, resolve_scanner  # noqa: E402
from core.config import REPO_ROOT, atomic_write_text, canonical_json, load_json  # noqa: E402
from study_2_2_views.views import VIEWS, render_all  # noqa: E402


def flag_rows(game_id: str, hits: list[dict]) -> list[dict]:
    """Flag-only scanner hits as type-blind rows (opaque game id, round, agent, field, kind, match)."""
    return [{"game_id": game_id, "round": h["round"], "agent": h["agent"], "where": h["where"],
             "kind": fh.get("kind", "unknown") if isinstance(fh, dict) else "unknown",
             "match": fh.get("match", "") if isinstance(fh, dict) else str(fh)}
            for h in hits if h["kind"] == "flag" for fh in h["flag_hits"]]


def load_mapping(labels_csv: Path, split_json: Path) -> dict[str, tuple]:
    split = load_json(split_json)
    which = {g: "dev" for g in split["dev"]} | {g: "test" for g in split["test"]}
    with open(labels_csv, encoding="utf-8", newline="") as f:
        return {r["game_id"]: (int(r["episode_type"]), which.get(r["game_id"], "unsplit")) for r in csv.DictReader(f)}


def load_mapping_unsplit(labels_csv: Path) -> dict[str, tuple]:
    """Game set WITHOUT a split (replication prereg §2): every game in one group, so C-mismatch partners are drawn
    within episode type across the whole set (never self)."""
    with open(labels_csv, encoding="utf-8", newline="") as f:
        return {r["game_id"]: (int(r["episode_type"]), "unsplit") for r in csv.DictReader(f)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "raw", help="folder of GameRecord .json files")
    ap.add_argument("--views", default=",".join(VIEWS), help=f"comma list from {','.join(VIEWS)}")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "views")
    ap.add_argument("--clean-out", type=Path, default=REPO_ROOT / "data")
    ap.add_argument("--setup-texts", type=Path, help="JSON list of setup texts (addenda with names filled, 4b line)")
    ap.add_argument("--labels", type=Path, help="data/labels.csv (only for C-mismatch)")
    ap.add_argument("--split", type=Path, help="data/split.json (only for C-mismatch)")
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--no-split", action="store_true",
                    help="game set without a split: C-mismatch within type across all games (needs --labels, "
                         "refuses --split)")
    ap.add_argument("--dry-run", action="store_true", help="print what would be written, write nothing")
    a = ap.parse_args(argv)
    if a.no_split and (a.split or not a.labels):
        ap.error("--no-split needs --labels and must not be given --split")

    views = [v.strip() for v in a.views.split(",") if v.strip()]
    bad = [v for v in views if v not in VIEWS]
    if bad:
        ap.error(f"unknown views {bad}")
    files = sorted(p for p in a.input.glob("*.json") if not p.name.startswith("."))
    setup = load_json(a.setup_texts) if a.setup_texts else []
    _, source = resolve_scanner()
    mapping = (load_mapping_unsplit(a.labels) if a.no_split
               else load_mapping(a.labels, a.split) if a.labels and a.split else None)
    print(f"{len(files)} game records in {a.input}; views {views}; scanner: {source}; "
          f"setup texts: {len(setup)}; C-mismatch mapping: {'yes' if mapping else 'no'}")
    if not setup:
        print("WARNING: no --setup-texts given: the 8-word copy check has nothing to compare against.")
    if a.dry_run:
        print(f"dry run: would write {len(files)} clean + {len(files)} clean_private files and up to "
              f"{len(files) * len(views)} view files to {a.out}")
        return 0

    cleans, privates, n_hits = [], {}, 0
    hits_path = a.clean_out / "clean" / "leak_hits.jsonl"
    flags_path = a.clean_out / "clean" / "leak_flags.jsonl"
    hit_lines, flag_lines = [], []
    for p in files:
        rec = json.loads(p.read_text(encoding="utf-8"))
        c, priv, hits = clean_game(rec, setup)
        cleans.append(c)
        privates[c.game_id] = priv
        atomic_write_text(a.clean_out / "clean" / f"{c.game_id}.json", canonical_json(c.to_dict()))
        atomic_write_text(a.clean_out / "clean_private" / f"{c.game_id}.json", canonical_json(priv.to_dict()))
        hit_lines += [json.dumps({"game_id": c.game_id, **h}, sort_keys=True, ensure_ascii=False)
                      for h in hits if h["kind"] != "flag"]
        flag_lines += flag_rows(c.game_id, hits)
        n_hits += c.leak_scan["hits"]
    atomic_write_text(hits_path, "".join(x + "\n" for x in hit_lines))
    atomic_write_text(flags_path, "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in flag_lines))
    by_kind = Counter(r["kind"] for r in flag_lines)
    man = render_all(cleans, a.out, views, privates=privates, mapping=mapping, seed=a.seed)
    print(f"cleaned {len(cleans)} games ({n_hits} removing hits, log: {hits_path}; {len(flag_lines)} flag-only hits "
          f"{dict(by_kind)}, log: {flags_path}); wrote {len(man['files'])} view files, skipped {len(man['skipped'])}; "
          f"manifest: {a.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
