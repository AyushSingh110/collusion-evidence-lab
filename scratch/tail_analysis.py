import json
for r in json.load(open("results/games_analysis.json")):
    print(r["model"], r["type"], "calls", r["calls"], "fail", r["failures"], "wall_min", r["wall_min"], "uptake", r["uptake_rate"], r["uptake_pass"],
          "reveals", len(r["public_reveal"]), "leaks", len(r["leaks"]),
          {k: (round(v["focal"], 2), v["strictly_top"], round(v["max_other"], 2)) for k, v in r["metrics"].items()}, r["actions"])
