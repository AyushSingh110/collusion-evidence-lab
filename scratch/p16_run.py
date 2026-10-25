"""Task 16 Follow-up 1 runner (prereg configs/prereg_followup1_pair_order.md, commit 496fc28).

Two arms in ONE session, interleaved call by call, sample_idx 1 in both:
  rot   = monitor_v3_pairs_ctx16k_rot, pairs in a per-call permuted order (seed sha256(game|view|followup1))
  fixed = monitor_v3_pairs_ctx16k (frozen, unchanged), frozen fixed order
Cell order = sorted (game, view) over the 24 test games x V1-V4, shuffled by random.Random(20261023), saved to
runs/followup1/run_order.json before the first call. Per cell: rot call, then fixed call.
Failures (transport / parse / truncation) are written as data and never re-run (a resumed run skips them).

  conda run --no-capture-output -n collusion-lab python -u -B scratch/p16_run.py [--limit N]
"""
import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT, load_pins, load_run_defaults, text_file_sha256, CONFIGS  # noqa: E402
from core.llm import CachedLLM, OllamaTransport  # noqa: E402
from study_2_2_views.monitor import (PROMPTS, code_version, emitted_key_order, load_config,  # noqa: E402
                                     permuted_pair_order, score_view)

OUT = REPO_ROOT / "runs/followup1"
VIEWS = ("V1", "V2", "V3", "V4")
SAMPLE_IDX, ORDER_SEED, SALT = 1, 20261023, "followup1"
PREREG_COMMIT = "496fc28279f357db95b57f527d851f61ad23710f"
ARMS = {"rot": "monitor_v3_pairs_ctx16k_rot", "fixed": "monitor_v3_pairs_ctx16k"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="stop after this many NEW calls (timing measurement)")
    a = ap.parse_args()
    test = sorted(json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["test"])
    cells = sorted((g, v) for g in test for v in VIEWS)
    random.Random(ORDER_SEED).shuffle(cells)
    OUT.mkdir(parents=True, exist_ok=True)
    ro = OUT / "run_order.json"
    if ro.exists():
        assert [tuple(c) for c in json.loads(ro.read_text(encoding="utf-8"))["cells"]] == cells, "run order changed"
    else:
        ro.write_text(json.dumps({"seed": ORDER_SEED, "rule": "random.Random(20261023).shuffle(sorted (game, view))",
                                  "per_cell": ["rot", "fixed"], "cells": cells}, indent=1), encoding="utf-8")

    cfg = {arm: load_config(manifest=PROMPTS[p]) for arm, p in ARMS.items()}
    rd = load_run_defaults()
    llm = CachedLLM(transport=OllamaTransport(rd["llm"]["base_url"]), pins=load_pins(), models=[cfg["rot"].model],
                    cache_dir=REPO_ROOT / "cache" / "llm", timeout_s=rd["llm"]["timeout_s"],
                    retry_delays_s=rd["llm"]["retry_delays_s"], keep_alive=rd["llm"]["keep_alive"])
    files = {arm: OUT / f"{arm}.jsonl" for arm in ARMS}
    done = {arm: {(d["game_id"], d["view"]) for d in map(json.loads, f.read_text(encoding="utf-8").splitlines())}
            if f.exists() else set() for arm, f in files.items()}
    man_path = OUT / "manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {
        "run_id": "followup1", "prereg": "configs/prereg_followup1_pair_order.md", "prereg_commit": PREREG_COMMIT,
        "arms": {arm: {"prompt_version": c.prompt_version, "template_sha256": c.template_sha256,
                       "manifest_file_sha256": text_file_sha256(CONFIGS / "monitor" / PROMPTS[ARMS[arm]]),
                       "monitor_manifest_sha256": c.manifest_sha256} for arm, c in cfg.items()},
        "model": cfg["rot"].model, "digest": llm.digests.get(cfg["rot"].model), "ollama_version": llm.ollama_version,
        "temperature": 0.0, "num_ctx": cfg["rot"].num_ctx, "num_predict": cfg["rot"].num_predict,
        "sample_idx": SAMPLE_IDX, "seed_rule": "sha256(game_id|view|sample_idx) mod 2^31",
        "pair_order_rule": f'random.Random(int(sha256(game_id|view|{SALT}),16)).shuffle(canonical)', "sessions": []}
    assert all(c.num_ctx == 16384 and c.temperature == 0.0 and c.num_predict == 250 for c in cfg.values())
    session = {"start_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "machine_id": llm.machine_id,
               "gpu": llm.gpu, **code_version()}
    n_new = 0
    for pos, (gid, view) in enumerate(cells):
        text = (REPO_ROOT / "data/views" / view / f"{gid}.txt").read_text(encoding="utf-8")
        for arm in ARMS:
            if (gid, view) in done[arm]:
                continue
            if a.limit is not None and n_new >= a.limit:
                break
            order = permuted_pair_order(cfg[arm].pair_order, gid, view, SALT) if arm == "rot" else None
            line = score_view(text, view, llm, cfg[arm], game_id=gid, sample_idx=SAMPLE_IDX, pair_order=order)
            if arm == "fixed":
                line["presented_pair_order"] = list(cfg[arm].pair_order)
                hit = llm._lookup(line["cache_key"]) if line["cache_key"] else None
                line["emitted_pair_order"] = emitted_key_order(hit["result"].get("content")) if hit else None
            line.update({"run_id": "followup1", "arm": arm, "run_order_pos": pos,
                         "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            with open(files[arm], "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")
            done[arm].add((gid, view))
            n_new += 1
            print(f"[{pos + 1}/96 {arm:5}] {view} {gid}: score={line['score']} pair={line['suspected_pair']} "
                  f"parse_ok={line['parse_ok']} trunc={line['truncation_suspect']} err={line['error']} "
                  f"latency={line['latency']} hit={line['cache_hit']}", flush=True)
        if a.limit is not None and n_new >= a.limit:
            break
    session.update({"end_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "new_calls": n_new})
    man["sessions"].append(session)
    man_path.write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"done: {n_new} new calls; rot {len(done['rot'])}/96, fixed {len(done['fixed'])}/96")
    return 0


if __name__ == "__main__":
    sys.exit(main())
