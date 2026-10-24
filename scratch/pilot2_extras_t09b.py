"""Task 09b extras (no model calls): per-game non-English counts in every field, and Type 1 excerpts for pilot 2.

  PYTHONIOENCODING=utf-8 conda run --no-capture-output -n collusion-lab python -B scratch/pilot2_extras_t09b.py [raw_dir]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.evidence import rq01 as R  # noqa: E402

raw = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/pilot2")
for p in sorted(raw.glob("g_*.json")):
    if p.name.endswith(".partial.json"):
        continue
    rec = json.loads(p.read_text(encoding="utf-8"))
    g, lab = R.from_record(rec), R.labels_from_record(rec)
    f = R.norm_pair(lab.focal_pair, g.agents)
    n = {"public": [0, 0], "channel": [0, 0], "stage1": [0, 0], "stage3": [0, 0]}
    for Rr in rec["rounds"]:
        for e in Rr["stage2"]:
            n["public"][1] += 1
            n["public"][0] += R.is_non_english(e.get("message"))
        for c in Rr.get("channel", []):
            n["channel"][1] += 1
            n["channel"][0] += R.is_non_english(c.get("text"))
        for k in ("stage1", "stage3"):
            for v in Rr[k].values():
                n[k][1] += 1
                n[k][0] += R.is_non_english(v.get("reasoning"))
    u1, u2 = R.uptake(g, f), R.uptake_v2(g, f)
    print(f"== {g.game_id} type {lab.episode_type} focal {'-'.join(f)} lang_line={rec['config'].get('language_line')} "
          f"non-English: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in n.items())
          + f" | v1 {u1['rate']:.3f} v2 {u2['rate']:.3f} non_en_cells {len(u2['non_english_cells'])}")
    if lab.episode_type != 1:
        continue
    for Rr in rec["rounds"]:
        acts = "".join("G" if Rr["stage3"][a]["choice"] == "GO" else "S" for a in rec["config"]["agents"])
        print(f"  R{Rr['round']} JMQTZ={acts} n_go={Rr['outcome']['n_go']}")
        if Rr["round"] in (1, 4, 7):
            for c in Rr.get("channel", []):
                print(f"     CH {c['from']}: {(c.get('text') or '')[:170]}")
            for a in f:
                print(f"     PLAN {a}: {(Rr['stage1'][a].get('reasoning') or '')[:170]}")
            for e in Rr["stage2"]:
                if e["agent"] in f:
                    print(f"     PUB {e['agent']}: {(e.get('message') or '')[:170]}")
