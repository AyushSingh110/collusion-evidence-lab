"""Task 21: per-view run statistics of the frozen llama monitor on the replication (no model calls).

  conda run -n collusion-lab python -B scratch/p21_run_stats.py
"""
import collections
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402

rows = [json.loads(x) for x in (REPO_ROOT / "runs/replication_llama/outputs/monitor.jsonl").read_text(encoding="utf-8")
        .splitlines() if x.strip()]
by = collections.defaultdict(list)
for d in rows:
    by[d["view"]].append(d)
print("| View | Lines | parse_fail | Truncation | Missing score | Length cuts | Mean latency s | Max prompt_eval |")
print("|---|---|---|---|---|---|---|---|")
for v in ("V1", "V2", "V3", "V4", "V5", "C-mismatch", "C-length", "C-shuffled"):
    L = by[v]
    print(f"| {v} | {len(L)} | {sum(not d['parse_ok'] for d in L)} | {sum(d['truncation_suspect'] for d in L)} | "
          f"{sum(d['score'] is None for d in L)} | {sum(d['done_reason'] == 'length' for d in L)} | "
          f"{st.mean(d['latency'] for d in L if d['latency']):.1f} | {max(d['prompt_eval_count'] or 0 for d in L)} |")
print("total", len(rows), "| samples", sorted({d["sample_idx"] for d in rows}), "| digests",
      sorted({d["digest"][:12] for d in rows}), "| prompt", sorted({d["prompt_version"] for d in rows}),
      "| cache hits", sum(d["cache_hit"] for d in rows), "| distinct games", len({d["game_id"] for d in rows}))
print("sum latency min", round(sum(d["latency"] or 0 for d in rows) / 60, 1))
