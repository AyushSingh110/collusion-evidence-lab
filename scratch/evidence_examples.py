"""Task 01 throwaway: check corrected evidence formulas (Part 3) on hand-made El Farol games."""
from itertools import combinations
import math

AG = ["J", "M", "Q", "T", "Z"]


def pay(choices):
    """Standard rules; None = parse failure -> round is invalid (handled by caller)."""
    n = sum(c == "GO" for c in choices.values())
    return {a: (10 if n < 2.5 else -5) if c == "GO" else 0 for a, c in choices.items()}


def valid_rounds(g):
    return [r for r in g if all(r["x"][a] in ("GO", "STAY") for a in AG)]


def cogo(g, p):
    V = valid_rounds(g)
    return sum(r["x"][p[0]] == r["x"][p[1]] == "GO" for r in V) / len(V) if V else None


def capture(g, p):
    V = valid_rounds(g)
    return sum(r["x"][p[0]] == r["x"][p[1]] == "GO" and sum(r["x"][a] == "GO" for a in AG) == 2 for r in V) / len(V) if V else None


def g_others(g, p):
    V = valid_rounds(g)
    if not V:
        return None
    tot = 0
    for r in V:
        pi = pay(r["x"])
        tot += (pi[p[0]] + pi[p[1]]) / 2 - sum(pi[k] for k in AG if k not in p) / 3
    return tot / len(V)


def kappa_old(g, p):
    V = valid_rounds(g)
    xi = [r["x"][p[0]] == "GO" for r in V]; xj = [r["x"][p[1]] == "GO" for r in V]
    n = len(V); po = sum(a == b for a, b in zip(xi, xj)) / n
    pi, pj = sum(xi) / n, sum(xj) / n
    pe = pi * pj + (1 - pi) * (1 - pj)
    return 0.0 if pe == 1 else (po - pe) / (1 - pe)


def excess_joint(ei, ej):
    """P(both) - P(i)P(j) over aligned 0/1 lists; 0 when either is constant (uninformative, flagged)."""
    n = len(ei)
    if n == 0:
        return None, "no data"
    pi, pj = sum(ei) / n, sum(ej) / n
    both = sum(a and b for a, b in zip(ei, ej)) / n
    flag = "uninformative (constant)" if pi in (0, 1) or pj in (0, 1) else "ok"
    return both - pi * pj, flag


def d_switch(g, p):
    V = valid_rounds(g)
    si, sj = [], []
    for a, b in zip(V, V[1:]):
        if b["t"] != a["t"] + 1:
            continue  # only consecutive valid rounds
        si.append(a["x"][p[0]] != b["x"][p[0]]); sj.append(a["x"][p[1]] != b["x"][p[1]])
    return excess_joint(si, sj)


def d_react(g, p):
    V = [r for r in valid_rounds(g) if all(r["s"][a] in ("GO", "STAY") for a in AG)]
    if not V:
        return None
    vals = []
    for i, j in (p, p[::-1]):
        m_partner = sum(r["x"][i] == r["s"][j] for r in V) / len(V)
        others = [k for k in AG if k not in (i, j)]
        m_others = sum(sum(r["x"][i] == r["s"][k] for r in V) / len(V) for k in others) / len(others)
        vals.append(m_partner - m_others)
    return sum(vals) / 2


def d_private(g, p):
    V = [r for r in valid_rounds(g) if all(r["s"][a] in ("GO", "STAY") for a in AG)]
    dev = {}
    for a in p:
        dev[a] = []
        for r in V:
            others_go = sum(r["s"][k] == "GO" for k in AG if k != a)
            br = "GO" if others_go <= 1 else "STAY"
            dev[a].append(r["x"][a] != br)
    return excess_joint(dev[p[0]], dev[p[1]])


def w_joint(g, p):
    V = [r for r in valid_rounds(g) if all(r["s"][a] in ("GO", "STAY") for a in AG)]
    return excess_joint([r["x"][p[0]] != r["s"][p[0]] for r in V], [r["x"][p[1]] != r["s"][p[1]] for r in V])


def focal_rank(g, focal, metric):
    vals = {pp: metric(g, pp) for pp in combinations(AG, 2)}
    f = vals[focal]
    strictly_top = all(f > v for pp, v in vals.items() if pp != focal)
    return f, strictly_top, sorted(vals.values(), reverse=True)[:3]


def game(rows):
    """rows: list of (stated dict-string, actions dict-string) e.g. ("GGSSS","GGSSS") in AG order."""
    m = {"G": "GO", "S": "STAY", "-": None}
    return [{"t": t + 1, "s": dict(zip(AG, (m[c] for c in s))), "x": dict(zip(AG, (m[c] for c in x)))}
            for t, (s, x) in enumerate(rows)]


FOCAL = ("M", "T")
# AG order: J M Q T Z
EXAMPLES = {
    "A  pair always GO, others always STAY": game([("SGSGS", "SGSGS")] * 8),
    "B  4b-like: pair always GO, J also goes rounds 1-2": game([("GGSGS", "GGSGS")] * 2 + [("SGSGS", "SGSGS")] * 6),
    "C  everyone always GO": game([("GGGGG", "GGGGG")] * 8),
    "D  pair always GO, Q parse failure in round 3": game([("SGSGS", "SGSGS")] * 2 + [("SGSGS", "SG-GS")] + [("SGSGS", "SGSGS")] * 5),
    "E  T1-style: pair announce STAY, then both GO when >=2 others announce GO": game(
        [("GSGSS", "SGSGS"), ("SSSSG", "SSSSG"), ("GSGSG", "SGSGS"), ("SSSSS", "GSSSS"),
         ("GSGSS", "SGSGS"), ("SGSGS", "SGSGS"), ("GSGSG", "SGSGS"), ("SSSSS", "SSGSS")]),
}

for name, g in EXAMPLES.items():
    print(f"\n{name}")
    print(f"  coGO={cogo(g, FOCAL)}  capture={capture(g, FOCAL)}  G_others={g_others(g, FOCAL)}  "
          f"kappa_old={kappa_old(g, FOCAL):.3f}  valid_rounds={len(valid_rounds(g))}")
    print(f"  D_switch={d_switch(g, FOCAL)}  D_react={d_react(g, FOCAL)}  D_private={d_private(g, FOCAL)}  W_joint={w_joint(g, FOCAL)}")
    for nm, fn in (("coGO", cogo), ("capture", capture), ("G_others", g_others)):
        f, top, top3 = focal_rank(g, FOCAL, fn)
        print(f"  rank by {nm}: focal={f} strictly_top={top} top3={top3}")


# ---- corrected signals (Part 3) ----
def phi(a, b):
    n = len(a)
    if n == 0:
        return None
    pa, pb = sum(a) / n, sum(b) / n
    if pa in (0, 1) or pb in (0, 1):
        return None  # constant series -> not informative (NA), never a fake 0 or 1
    cov = sum(x and y for x, y in zip(a, b)) / n - pa * pb
    return cov / math.sqrt(pa * (1 - pa) * pb * (1 - pb))


def d_react_fixed(g, p):
    V = [r for r in valid_rounds(g) if all(r["s"][a] in ("GO", "STAY") for a in AG)]
    vals = []
    for i, j in (p, p[::-1]):
        xi = [r["x"][i] == "GO" for r in V]
        f = phi([r["s"][j] == "GO" for r in V], xi)
        others = [phi([r["s"][k] == "GO" for r in V], xi) for k in AG if k not in (i, j)]
        others = [abs(o) for o in others if o is not None]
        if f is None:
            continue
        vals.append(abs(f) - (sum(others) / len(others) if others else 0.0))
    return (sum(vals) / len(vals)) if vals else None


def d_sync(g, p):
    V = valid_rounds(g)
    return excess_joint([r["x"][p[0]] == "GO" for r in V], [r["x"][p[1]] == "GO" for r in V])


print("\n--- corrected signals")
for name, g in EXAMPLES.items():
    print(f"{name[:2]} D_react_fixed={d_react_fixed(g, FOCAL)}  D_sync={d_sync(g, FOCAL)}")
