from pathlib import Path
p = Path(__file__).resolve().parents[1] / "configs" / "prereg_rq01.md"
t = p.read_text(encoding="utf-8")
subs = [("| Outcome | Step | Re-run | Approx. time (3 laptops, 8 rounds, brevity cap; estimated) |",
         "| Outcome | Step | Re-run | Approx. time (2 laptops A + B, B ≈ 2.4× faster; 8 rounds; brevity cap; estimated) |"),
        ("| 4 Type 1 games | ≈ 45 min |", "| 4 Type 1 games | ≈ 30 min |"),
        ("| 4 Type 1 games | ≈ 5 + 45–60 min |", "| 4 Type 1 games | ≈ 5 + 30–45 min |"),
        ("| E2 more rounds (12) | 4 Type 1 games | ≈ 70 min |", "| E2 more rounds (12) | 4 Type 1 games | ≈ 45 min |"),
        ("| 8 games | ≈ 3 h dev + 1 h |", "| 8 games | ≈ 3 h dev + 1 h |")]
for old, new in subs:
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
