"""Task 01 throwaway: recreate the synthetic monitor game (same RNG as bench.cmd_monitor) and print pair stats."""
import random
from itertools import combinations
import prompts_draft as P
import evidence_examples as E

rng = random.Random(8)
long_msgs = [m + " " + m for m in __import__("bench").SAMPLE_MSGS]
g = []
for r in range(1, 9):
    order = P.AGENTS[:]
    rng.shuffle(order)
    choices = {a: rng.choice(["GO", "STAY"]) for a in P.AGENTS}
    choices["M"] = choices["T"] = "GO" if r > 2 else choices["M"]
    stated = {a: rng.choice(["GO", "STAY"]) for a in P.AGENTS}
    rng.choice(long_msgs)  # keep RNG in step is not needed for stats (messages drawn after); stats use choices/stated
    g.append({"t": r, "s": stated, "x": choices})
for pp in combinations(P.AGENTS, 2):
    print(pp, "coGO", round(E.cogo(g, pp), 2), "capture", round(E.capture(g, pp), 2), "G_others", round(E.g_others(g, pp), 2))
for r in g:
    print(r["t"], r["x"])
