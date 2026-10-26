"""Task 23 helper: print the structure and the headline values of the replication result files (read-only).

  conda run -n collusion-lab python -B scratch/p23_inspect.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT  # noqa: E402


def show(o, pre="", depth=0, maxd=3):
    if depth > maxd:
        return
    if isinstance(o, dict):
        for k, v in list(o.items())[:40]:
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}: {type(v).__name__}({len(v)})")
                show(v, pre + "  ", depth + 1, maxd)
            else:
                print(f"{pre}{k}: {str(v)[:90]}")
    elif isinstance(o, list) and o:
        print(f"{pre}[0]:")
        show(o[0], pre + "  ", depth + 1, maxd)


for p in ("runs/replication_granite/results.json", "runs/replication_23/results.json"):
    print(f"\n######## {p}")
    show(json.loads((REPO_ROOT / p).read_text(encoding="utf-8")), maxd=2)

G = json.loads((REPO_ROOT / "runs/replication_granite/results.json").read_text(encoding="utf-8"))
print("\n######## granite descriptive (llama) keys")
show(G["primary"]["descriptive"]["llama"], maxd=1)
print("\n######## G hypotheses")
for k, v in G["primary"]["hypotheses"].items():
    print(k, json.dumps(v)[:400])
