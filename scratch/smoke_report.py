"""Task 04 L2: analyse the smoke game record(s) in runs/smoke/raw/ with the project's own code."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.clean.leaks import scan_record  # noqa: E402
from core.evidence import rq01  # noqa: E402
from core.schema import validate_game  # noqa: E402

for f in sorted((ROOT / "runs" / (sys.argv[1] if len(sys.argv) > 1 else "smoke") / "raw").glob("*.json")):
    if f.name.endswith(".partial.json"):
        print("UNFINISHED", f)
        continue
    rec = json.loads(f.read_text(encoding="utf-8"))
    g, lab = rq01.from_record(rec), rq01.labels_from_record(rec)
    calls = [c["call"] for r in rec["rounds"] for c in
             list(r["stage1"].values()) + r["channel"] + r["stage2"] + list(r["stage3"].values())]
    up = rq01.uptake(g, lab.focal_pair)
    rv = rq01.public_reveals(g, lab.focal_pair)
    leaks = scan_record(rec)
    per_round_s = {}
    for r in rec["rounds"]:
        cs = list(r["stage1"].values()) + r["channel"] + r["stage2"] + list(r["stage3"].values())
        per_round_s[r["round"]] = round(sum(c["call"]["latency_s"] or 0 for c in cs), 1)
    print(json.dumps({
        "game_id": rec["game_id"], "type": lab.episode_type, "focal": lab.focal_pair, "validate": validate_game(rec),
        "calls": len(calls), "parse_failures": len(rec["failures"]), "failures": rec["failures"],
        "truncation_suspect": sum(bool(c["truncation_suspect"]) for c in calls),
        "done_reason_length": sum(c["done_reason"] == "length" for c in calls),
        "max_gen_tokens": max(c["eval_count"] or 0 for c in calls),
        "leak_hits": leaks, "public_reveals": {"count": rv["count"], "n": rv["n_messages"], "hits": rv["hits"]},
        "uptake": {"rate": up["rate"], "per_agent": up["per_agent"], "pass": up["pass"],
                   "cells": [{k: c[k] for k in ("round", "agent", "channel_joint", "plan_partner", "U")} for c in up["cells"]]},
        "wall_s": rec["wall_s"], "call_seconds_per_round": per_round_s,
        "actions": [{a: r["stage3"][a]["choice"] for a in g.agents} for r in rec["rounds"]],
        "usage": rec["usage"], "prompts": rec["prompts"],
    }, indent=1))
    print("\n=== TRANSCRIPT (focal pair) ===")
    for r in rec["rounds"]:
        print(f"--- round {r['round']} order {r['order']}")
        for a in lab.focal_pair:
            print(f"  [S1 {a}] {r['stage1'][a]['intended_action']}: {r['stage1'][a]['reasoning']}")
        for c in r["channel"]:
            print(f"  [CH-{c['exchange']} {c['from']}] {c['text']}")
        for e in r["stage2"]:
            print(f"  [S2{'*' if e['agent'] in lab.focal_pair else ' '}{e['agent']}] {e['stated_action']}: {e['message']}")
        print("  [S3]", {a: r["stage3"][a]["choice"] for a in g.agents}, "payoffs", r["outcome"]["payoffs_public"])
