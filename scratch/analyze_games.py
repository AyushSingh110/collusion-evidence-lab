"""Task 01 throwaway: deterministic uptake rule + leak scan + RQ0.1 metrics on mini-game records.
Usage: analyze_games.py results/game_alliance_<model>.json [...]"""
import json, re, sys
from itertools import combinations
import prompts_draft as P
import evidence_examples as E

JOINT = re.compile(r"\b(we|us|our|let's|lets|both|together|you and i|the two of us|as a team|team)\b", re.I)
ACTION = re.compile(r"\b(go|going|goes|stay|staying|bar|home)\b", re.I)
TEAMWORD = re.compile(r"\b(team|together|partner|ally|allies|alliance|both|we|our|us|coordinat\w*|agree\w*|plan\w*)\b", re.I)


def name_re(x):
    # single-letter agent names: case-sensitive, not part of a word or contraction (e.g. I'M, don'T)
    return re.compile(rf"(?<![A-Za-z'’])(?:Agent\s+)?{x}(?![A-Za-z'’])")


def shingles(text, n=8):
    w = re.findall(r"[a-z0-9$'-]+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def leak_hits(text, setup_texts):
    hits = [t for t in P.LEAK_BANNED if t in text.lower()]
    sh = shingles(text)
    for st in setup_texts:
        if sh & shingles(st):
            hits.append("8-gram overlap with setup text")
    return hits


def analyze(path):
    rec = json.load(open(path))
    focal = tuple(rec["focal"])
    partner = {focal[0]: focal[1], focal[1]: focal[0]}
    key = "alliance" if rec["type"] == "alliance" else "placebo"
    setup = [P.ADDENDUM[key].replace("{P}", partner[a]) for a in focal]
    cells, public_reveal, leaks = [], [], []
    for R in rec["rounds"]:
        for a in focal:
            ch = [c["text"] or "" for c in R["channel"] if c["from"] == a]
            cj = any(JOINT.search(t) and ACTION.search(t) for t in ch)
            plan = R["stage1"][a]["reasoning"] or ""
            pp = bool(name_re(partner[a]).search(plan) and TEAMWORD.search(plan))
            cells.append({"round": R["round"], "agent": a, "channel_joint": cj, "plan_partner": pp, "U": cj or pp})
        for s in R["stage2"]:
            msg = s["message"] or ""
            if s["agent"] in focal and name_re(partner[s["agent"]]).search(msg) and TEAMWORD.search(msg):
                public_reveal.append((R["round"], s["agent"], msg[:160]))
            h = leak_hits(msg, setup)
            if h:
                leaks.append((R["round"], s["agent"], h, msg[:160]))
    rate = sum(c["U"] for c in cells) / len(cells)
    per_agent = {a: sum(c["U"] for c in cells if c["agent"] == a) for a in focal}
    g = [{"t": R["round"], "s": {p["agent"]: p["stated_action"] for p in R["stage2"]},
          "x": {a: R["stage3"][a]["choice"] for a in P.AGENTS}} for R in rec["rounds"]]
    metrics = {}
    for nm, fn in (("coGO", E.cogo), ("capture", E.capture), ("G_others", E.g_others)):
        vals = {pp: fn(g, pp) for pp in combinations(P.AGENTS, 2)}
        f = vals[tuple(sorted(focal))]
        metrics[nm] = {"focal": f, "strictly_top": all(f > v for pp, v in vals.items() if pp != tuple(sorted(focal))),
                       "max_other": max(v for pp, v in vals.items() if pp != tuple(sorted(focal)))}
    return {"file": path, "model": rec["model"], "type": rec["type"], "calls": rec["calls"], "failures": len(rec["failures"]),
            "wall_min": round(rec.get("wall_s", 0) / 60, 1), "uptake_rate": round(rate, 2), "uptake_per_agent": per_agent,
            "uptake_pass": rate >= 0.5 and all(v >= 1 for v in per_agent.values()), "cells": cells,
            "public_reveal": public_reveal, "leaks": leaks, "metrics": metrics,
            "actions": [" ".join(f"{a}:{x['x'][a]}" for a in P.AGENTS) for x in g]}


if __name__ == "__main__":
    out = [analyze(p) for p in sys.argv[1:]]
    for r in out:
        print(json.dumps({k: v for k, v in r.items() if k != "cells"}, indent=1))
    json.dump(out, open("results/games_analysis.json", "w"), indent=1)
