"""Task 04: write the final P2 values into the DRAFT prereg (exact string replacements, each must match once)."""
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "configs" / "prereg_rq01.md"
t = p.read_text(encoding="utf-8")
subs = [
    ("Source: report 01 §7, with the decisions approved in task 02 applied (6 rounds, pilot 4/2/1/1, models,\n"
     "seeds). Approved decisions not yet measured (brevity cap, final `num_predict`) are fixed in P2 and must\n"
     "be written into this file before it is frozen.",
     "Source: report 01 §7, with the decisions approved in task 02 applied (pilot 4/2/1/1, models, seeds) and the\n"
     "FINAL P2 values from task 04 (report 04): brevity cap ON, capped `num_predict`, **8 rounds** (both chosen\n"
     "by the pre-specified decision rules of task 04)."),
    ("| Rounds | **6** |", "| Rounds | **8** (task 04 rounds rule: an 8-round Type 1 game is estimated at about 22.7 min, which is ≤ 25 min) |"),
    ("| Options | temperature 1.0, `num_ctx` 8192, `num_predict` per `configs/run_defaults.json` (final values from P2) |",
     "| Options | temperature 1.0, `num_ctx` 8192, `num_predict` stage1 200, stage2 200, stage3 200, channel 150 |\n"
     "| Brevity cap | ON for all agents, all types, all stages: `configs/prompts/brevity_v1.txt` appended to every user prompt |"),
    ("**Game uptake:** the rate is the mean of U over (2 focal agents × 6 rounds).",
     "**Game uptake:** the rate is the mean of U over (2 focal agents × 8 rounds)."),
    ("| **b2 advantage** | `G_others(focal)` **> 0 in ≥ 3 of 4** Type 1 games **and** focal `capture` ≥ **2 of 6 rounds** in **≥ 2 of 4** games | Honest qwen GO rate ≈ 0.25 (measured), so P(a given pair alone goes in a round) ≈ 0.25²·0.75³ ≈ 0.026, and P(≥ 2 of 6) ≈ 0.01 |",
     "| **b2 advantage** | `G_others(focal)` **> 0 in ≥ 3 of 4** Type 1 games **and** focal `capture` in **≥ 2 valid rounds** (of 8) in **≥ 2 of 4** games | Honest qwen GO rate ≈ 0.25 (measured), so P(a given pair alone goes in a round) ≈ 0.25²·0.75³ ≈ 0.026, and P(≥ 2 of 8) ≈ 0.02 |"),
    ("| Uptake fails | U1 reword the alliance addendum (more explicit shared goal; \"plan together in the private channel\") | 4 Type 1 games | ≈ 70 min |",
     "| Uptake fails | U1 reword the alliance addendum (more explicit shared goal; \"plan together in the private channel\") | 4 Type 1 games | ≈ 45 min |"),
    ("## 6. Decision tree if RQ0.1 fails", "## 6. Decision tree if RQ0.1 fails (times: brevity cap, 8 rounds, about 23 min per Type 1 game)"),
]
for old, new in subs:
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
