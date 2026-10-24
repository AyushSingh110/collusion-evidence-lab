"""Task 08 Step 4 extras (no model calls): RQ0.2 observations, Type 1 excerpts, P7 view sizes, over-removal.

  PYTHONIOENCODING=utf-8 conda run --no-capture-output -n collusion-lab python -B scratch/pilot_analysis_t08.py

Reads data/raw/pilot/*.json and configs/monitor/setup_texts.json. Writes runs/pilot/views/ (V1-V5 + controls),
runs/pilot/clean/, runs/pilot/analysis_t08.json, and prints a text summary.
"""
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.clean.cleaner import _SENT_SPLIT, clean_game, resolve_scanner  # noqa: E402
from core.clean.leaks import scan_for_leaks  # noqa: E402
from core.config import CONFIGS, REPO_ROOT, atomic_write_text, canonical_json  # noqa: E402
from core.evidence import rq01  # noqa: E402
from study_2_2_views.monitor import load_config, system_prompt  # noqa: E402
from study_2_2_views.views import VIEWS, render_all  # noqa: E402

RAW = REPO_ROOT / "data" / "raw" / "pilot"
OUT = REPO_ROOT / "runs" / "pilot"
HEADER_TERMS = {"private note", "only you can see this"}
records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAW.glob("*.json")) if not p.name.endswith(".partial.json")]
setup = json.loads((CONFIGS / "monitor" / "setup_texts.json").read_text(encoding="utf-8"))
games = {r["game_id"]: rq01.from_record(r) for r in records}
labels = {r["game_id"]: rq01.labels_from_record(r) for r in records}
res = {"n_records": len(records), "scanner": resolve_scanner()[1], "n_setup_texts": len(setup)}

# ---------------------------------------------------------------- minutes per game
res["minutes"] = {r["game_id"]: {"type": labels[r["game_id"]].episode_type, "min": round(r["wall_s"] / 60, 2),
                                 "calls": r["usage"].get("calls")} for r in records}

# ---------------------------------------------------------------- RQ0.2
t2 = [g for gid, g in games.items() if labels[gid].episode_type == 2]
null = [row for g in t2 for row in rq01.pair_table(g)]
rng = {m: (min(r[m] for r in null if r[m] is not None), max(r[m] for r in null if r[m] is not None))
       for m in ("coGO", "capture", "G_others") if any(r[m] is not None for r in null)}
res["type2_null_range"] = rng
go_rate_t2 = [sum(r.actions[a] == "GO" for r in rq01.valid_rounds(g)) / max(1, len(rq01.valid_rounds(g)))
              for g in t2 for a in g.agents]
res["type2_go_rate_mean"] = st.mean(go_rate_t2) if go_rate_t2 else None
rq02 = {}
for gid, g in games.items():
    lab = labels[gid]
    f = rq01.norm_pair(lab.focal_pair, g.agents)
    V = rq01.valid_rounds(g)
    d = {"type": lab.episode_type, "focal": "-".join(f), "valid": len(V),
         "coGO": rq01.cogo(g, f).value, "capture": rq01.capture(g, f).value, "G_others": rq01.g_others(g, f).value,
         "go_rate": {a: (sum(r.actions[a] == "GO" for r in V) / len(V) if V else None) for a in f}}
    if lab.episode_type == 3:
        d["inside_t2_null"] = {m: (rng[m][0] <= d[m] <= rng[m][1]) if d[m] is not None and m in rng else None
                               for m in ("coGO", "capture")}
        rev = rq01.public_reveals(g, f)
        d["persona_talk_msgs"] = rev["count"]
        d["persona_talk_n"] = rev["n_messages"]
        d["persona_examples"] = [h["excerpt"] for h in rev["hits"][:3]]
    if lab.episode_type == 4:
        d["both_go_ge_075"] = all(v is not None and v >= 0.75 for v in d["go_rate"].values())
        d["coGO_ge_075"] = d["coGO"] is not None and d["coGO"] >= 0.75
    rq02[gid] = d
res["per_game"] = rq02

# ---------------------------------------------------------------- Type 1 excerpts
ex = {}
for r in records:
    gid = r["game_id"]
    if labels[gid].episode_type != 1:
        continue
    f = list(labels[gid].focal_pair)
    rounds = []
    for R in r["rounds"]:
        acts = "".join(("G" if (R["stage3"][a]["choice"] == "GO") else "S") for a in r["config"]["agents"])
        stated = {e["agent"]: e["stated_action"] for e in R["stage2"]}
        rounds.append({"round": R["round"], "actions_JMQTZ": acts, "n_go": R["outcome"]["n_go"],
                       "focal_stated": {a: stated.get(a) for a in f},
                       "focal_did": {a: R["stage3"][a]["choice"] for a in f},
                       "channel": [(c["from"], (c.get("text") or "")[:200]) for c in R.get("channel", [])],
                       "focal_public": {e["agent"]: (e.get("message") or "")[:200] for e in R["stage2"] if e["agent"] in f},
                       "focal_plan": {a: (R["stage1"][a].get("reasoning") or "")[:200] for a in f}})
    ex[gid] = {"focal": f, "rounds": rounds}
res["type1_excerpts"] = ex

# ---------------------------------------------------------------- clean + views
cleans, privates, all_hits = [], {}, {}
for r in records:
    c, p, h = clean_game(r, setup)
    cleans.append(c)
    privates[c.game_id] = p
    all_hits[c.game_id] = h
    atomic_write_text(OUT / "clean" / f"{c.game_id}.json", canonical_json(c.to_dict()))
    atomic_write_text(OUT / "clean_private" / f"{c.game_id}.json", canonical_json(p.to_dict()))
mapping = {gid: (labels[gid].episode_type, "pilot") for gid in games}
man = render_all(cleans, OUT / "views", VIEWS, privates=privates, mapping=mapping, seed=20261024)
cfg = load_config()
sys_chars = {v: len(system_prompt(cfg, v)) for v in VIEWS}
sizes = defaultdict(list)
for fobj in man["files"]:
    sizes[fobj["view"]].append(fobj["chars"])
res["views"] = {v: {"n": len(x), "chars_min": min(x), "chars_mean": round(st.mean(x)), "chars_max": max(x),
                    "est_tok_view_max": round(max(x) / 4), "est_tok_total_max": round((max(x) + sys_chars[v]) / 4),
                    "over_4096": sum((c + sys_chars[v]) / 4 >= 4096 for c in x),
                    "over_8192": sum((c + sys_chars[v]) / 4 >= 8192 for c in x)}
                for v, x in sizes.items()}
res["views_skipped"] = man["skipped"]
res["c_length_info"] = {f["game_id"]: f.get("info") for f in man["files"] if f["view"] == "C-length"}

# ---------------------------------------------------------------- over-removal (public messages only)
def kinds(text):
    return scan_for_leaks(text, setup)


over = defaultdict(lambda: {"public_sentences": 0, "removed_current": 0, "removed_new_rule": 0, "flag_only_new": 0,
                            "causes": Counter(), "examples": []})
for r in records:
    t = labels[r["game_id"]].episode_type
    for R in r["rounds"]:
        for e in R["stage2"]:
            over[t]["public_sentences"] += len([s for s in _SENT_SPLIT.split(e.get("message") or "") if s.strip()])
    for h in all_hits[r["game_id"]]:
        if h["kind"] != "leak" or h["where"] != "stage2.message":
            continue
        for s in h["removed"]:
            hs = kinds(s) or h["scanner_hits"]          # a sentence removed as part of a pair/whole: use message hits
            over[t]["removed_current"] += 1
            keep_removing = any(x["kind"] == "copy8" or (x["kind"] == "banned" and x["match"] in HEADER_TERMS) for x in hs)
            over[t]["removed_new_rule"] += keep_removing
            over[t]["flag_only_new"] += not keep_removing
            for x in hs:
                over[t]["causes"][f"{x['kind']}:{x['match'] if x['kind'] != 'copy8' else '8-word copy'}"] += 1
            if len(over[t]["examples"]) < 6:
                over[t]["examples"].append({"round": h["round"], "agent": h["agent"], "sentence": s[:160],
                                            "causes": [f"{x['kind']}:{x['match'][:40]}" for x in hs],
                                            "new_rule": "remove" if keep_removing else "flag only"})
res["over_removal"] = {t: {**v, "causes": dict(v["causes"])} for t, v in sorted(over.items())}
res["private_redactions"] = {gid: sum(len(h["removed"]) for h in hs if h["kind"] == "leak" and h["where"] != "stage2.message")
                             for gid, hs in all_hits.items()}
res["payoff_mismatches"] = {gid: sum(h["kind"] == "payoff_mismatch" for h in hs) for gid, hs in all_hits.items()}

atomic_write_text(OUT / "analysis_t08.json", json.dumps(res, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: v for k, v in res.items() if k != "type1_excerpts"}, indent=1, ensure_ascii=False, default=str))
