"""Task 06a Step 1: alliance_v3 = alliance_v2 + ' ' + collusion_hint_v1 (byte-exact); placebo_v3 = placebo_v2 + neutral sentence."""
from pathlib import Path
d = Path(__file__).resolve().parents[1] / "configs" / "prompts"
rd = lambda n: (d / n).read_text(encoding="utf-8").rstrip("\n")
(d / "alliance_v3.txt").write_text(rd("alliance_v2.txt") + " " + rd("collusion_hint_v1.txt") + "\n", encoding="utf-8", newline="\n")
p2 = rd("placebo_v2.txt")
anchor = "It was an ordinary, pleasant day."
extra = ("Later the clouds cleared, a few early stars appeared above the rooftops, and a cool breeze carried "
         "the smell of fresh bread from a bakery on the corner.")
assert p2.count(anchor) == 1
(d / "placebo_v3.txt").write_text(p2.replace(anchor, extra + " " + anchor) + "\n", encoding="utf-8", newline="\n")
print((d / "alliance_v3.txt").read_text(encoding="utf-8"))
print((d / "placebo_v3.txt").read_text(encoding="utf-8"))
