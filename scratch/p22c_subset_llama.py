"""Task 22C step 4: the V1-V4 subset of machine B's llama replication monitor output (amendment 1 §2: "V1-V4 subset of
its 384 calls"), so analyse_replication_granite.py (V1-V4 only, task 20C) can read it.

  conda run -n collusion-lab python -B scratch/p22c_subset_llama.py

Selects lines by the "view" field ONLY and writes their raw bytes unchanged (no re-serialisation, no score is read
or printed). Refuses to overwrite. Checks, exit 1 if any fails: exactly 192 lines = the 48 labelled games x V1-V4,
no duplicate (game, view), every subset line byte-identical to its line in B's original file. Prints both sha256.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402
from core.labels import read_labels  # noqa: E402

SRC = REPO_ROOT / "runs/replication_llama/outputs/monitor.jsonl"
DST = REPO_ROOT / "runs/replication_llama/outputs/monitor_V1-V4.jsonl"
LABELS = REPO_ROOT / "data/replication/labels.csv"
VIEWS = ("V1", "V2", "V3", "V4")

if DST.exists():
    sys.exit(f"REFUSED: {DST} exists; the subset is written once")
raw = SRC.read_bytes()
src_lines = [ln for ln in raw.split(b"\n") if ln.strip()]
keep = [ln for ln in src_lines if json.loads(ln)["view"] in VIEWS]
DST.write_bytes(b"".join(ln + b"\n" for ln in keep))

# ---- checks on the written file (read back from disk)
sub = [ln for ln in DST.read_bytes().split(b"\n") if ln.strip()]
keys = [(json.loads(ln)["game_id"], json.loads(ln)["view"]) for ln in sub]
games = {lb.game_id for lb in read_labels(LABELS)}
src_set = set(src_lines)
checks = {
    "source lines": len(src_lines),
    "subset lines == 192": len(sub) == 192,
    "covers 48 games x V1-V4 exactly": set(keys) == {(g, v) for g in games for v in VIEWS} and len(games) == 48,
    "no duplicate (game, view)": len(set(keys)) == len(keys),
    "every subset line byte-identical to a source line": all(ln in src_set for ln in sub),
    "views in subset": sorted({v for _, v in keys}),
    "source sha256": hashlib.sha256(raw).hexdigest(),
    "subset sha256": hashlib.sha256(DST.read_bytes()).hexdigest(),
}
for k, v in checks.items():
    print(f"{k}: {v}")
ok = all(v for k, v in checks.items() if k.endswith(("192", "exactly", "(game, view)", "source line")))
print("ALL CHECKS PASS" if ok else "CHECK FAILED - STOP")
sys.exit(0 if ok else 1)
