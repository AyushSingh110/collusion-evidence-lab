"""Task 06a: pre-freeze changes in the DRAFT prereg (exact replacements, each must match once)."""
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "configs" / "prereg_rq01.md"
t = p.read_text(encoding="utf-8")
subs = [
    ("| Prompts | harness builders (commit d585a7b) + history block + addenda v2 (report 01 §6), one slot for all types |",
     "| Prompts | harness builders (commit d585a7b) + history block + addenda in one slot for all types: Type 1 `alliance_v3.txt` (variant `collusion_v3_hint`), Type 2 `placebo_v3.txt`, Type 3 `persona_v1.txt`, Type 4b `incentive_4b_v1.txt` (sha256 in `configs/prompts/manifest.json`) |"),
    ("| Machines | assigned by `make_plan` (LPT on estimated minutes, per-machine speed factors from `scripts/selftest.py`) |",
     "| Machines | **A and B** (two laptops), assigned by `make_plan` (LPT on estimated minutes, per-machine speed factors from `scripts/selftest.py`) |"),
    ("| Uptake passes, b1 or b2 fails | E1 add `collusion_hint` (variant `collusion_hint`) | 4 Type 1 games | ≈ 45 min |\n", ""),
    ("## 7. RQ0.2 information from the same pilot (descriptive only)",
     "Step E1 (\"add `collusion_hint`\") no longer exists: the hint is already part of the standard Type 1 addendum\n"
     "(see \"Pre-freeze changes\"). The effect-failure path therefore starts at E2.\n\n"
     "## 7. RQ0.2 information from the same pilot (descriptive only)"),
]
for old, new in subs:
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)
t = t.rstrip("\n") + """

## 10. Pre-freeze changes (made while this file was DRAFT, before any pilot call)

| Date | Change | Evidence / reason |
|---|---|---|
| 2026-10-24 (task 04) | Uptake name pattern also matches possessives ("Agent M's plan", "M’s"); "I'M", "don'T", "MAYBE", "M'd" still do not match. Pattern in §4. | Report 03 §7 flagged that the earlier pattern missed possessives; 11 tests; recorded mini-games unchanged (uptake 1.00 / 0.00). |
| 2026-10-24 (task 06a) | **Hint in the standard Type 1 addendum.** Type 1 uses `alliance_v3.txt` = `alliance_v2.txt` + " " + `collusion_hint_v1.txt` (byte-exact), variant `collusion_v3_hint`. Former decision-tree step E1 removed. | Not pilot data: in all 3 live Type 1 games so far (report 01 mini-game, task 04 L2 smoke), the focal pair coordinated but others crowded the bar, so the pair never gained. Without the hint, b2 was predictably at risk. |
| 2026-10-24 (task 06a) | **Placebo v3.** Type 2 uses `placebo_v3.txt` = `placebo_v2.txt` + one neutral sentence (no agent names, actions, team words or banned terms). | Keeps the Type 2 placebo length-matched to the longer Type 1 addendum: measured with `qwen2.5:7b` (prompt_eval_count difference with a unique prefix), alliance_v3 = 130 tokens, placebo_v3 = 139 tokens, ratio 1.069 (within ±10%). |
| 2026-10-24 (task 06a) | Two machines (A, B) instead of three. | Machine C is not available. Does not change any game or criterion. |
"""
p.write_text(t + "\n", encoding="utf-8", newline="\n")
print("ok")
