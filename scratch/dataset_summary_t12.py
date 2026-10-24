"""Print the task-12 summary tables from runs/dataset_t12/quality_rq02.json (no model calls)."""
import json
import statistics as st
from collections import Counter, defaultdict

d = json.load(open("runs/dataset_t12/quality_rq02.json", encoding="utf-8"))
G = d["games"]
by_t = defaultdict(list)
for x in G:
    by_t[x["type"]].append(x)
print("games per (type, machine):", dict(Counter((x["type"], x["machine"]) for x in G)))
for m in ("A", "B"):
    mins = [x["minutes"] for x in G if x["machine"] == m]
    print(f"machine {m}: {len(mins)} games, total {sum(mins):.1f} min ({sum(mins) / 60:.2f} h), per game "
          f"min {min(mins):.1f} mean {st.mean(mins):.1f} max {max(mins):.1f}")
    for t in (1, 2, 3, 4):
        v = [x["minutes"] for x in G if x["machine"] == m and x["type"] == t]
        if v:
            print(f"   type {t}: n {len(v)}, mean {st.mean(v):.1f} min")
print("\nFAILURES per type and stage (count / calls, %):")
for t in (1, 2, 3, 4):
    calls, fails = Counter(), Counter()
    for x in by_t[t]:
        calls.update(x["calls_by_stage"])
        fails.update(x["failures_by_stage"])
    tot_c, tot_f = sum(calls.values()), sum(fails.values())
    print(f"  type {t}: total {tot_f}/{tot_c} = {100 * tot_f / tot_c:.2f}% | " + ", ".join(
        f"{s} {fails[s]}/{calls[s]} ({100 * fails[s] / calls[s]:.2f}%)" for s in sorted(calls) if calls[s]))
allc = sum(x["calls"] for x in G)
allf = sum(x["failures"] for x in G)
print(f"  ALL: {allf}/{allc} = {100 * allf / allc:.2f}%; kinds {dict(sum((Counter(x['failure_kinds']) for x in G), Counter()))}")
print("valid rounds per game:", dict(Counter(x["valid_rounds"] for x in G)))
qf = [x for x in G if x["quality_fail"]]
print("QUALITY-FAIL games (< 4 valid rounds or > 10% failed agent-stages):",
      [(x["game_id"], x["type"], x["valid_rounds"], round(100 * x["fail_share"], 1)) for x in qf])
print("max fail share per game: %.2f%%" % (100 * max(x["fail_share"] for x in G)))
print("\nNON-ENGLISH texts per game (games with any):")
for x in G:
    if any(x["non_english"].values()):
        print("  ", x["game_id"], "type", x["type"], x["non_english"])
print("  language_line on in all records:", all(x["language_line"] for x in G))
t1 = by_t[1]
rev, msgs = sum(x["reveals"] for x in t1), sum(x["focal_msgs"] for x in t1)
print(f"\nREVEALS Type 1: {rev}/{msgs} = {100 * rev / msgs:.1f}%; games with >= 1 reveal: "
      f"{sum(x['reveals'] > 0 for x in t1)}/{len(t1)}")
print("\nLEAK SCAN by type: removals (messages/fields with a removal, sentences) and removal kinds; flag-only by kind")
for t in (1, 2, 3, 4):
    rk, fk = Counter(), Counter()
    for x in by_t[t]:
        rk.update(x["removal_kinds"])
        fk.update(x["flags_by_kind"])
    print(f"  type {t}: removals {sum(x['removals'] for x in by_t[t])} fields / {sum(x['removed_sentences'] for x in by_t[t])}"
          f" sentences, kinds {dict(rk)} | flags {dict(fk)}")
print("\nMANIPULATION CHECK (Type 1):")
for x in sorted(t1, key=lambda x: x["game_id"]):
    print(f"  {x['game_id']} {x['machine']} {x['focal']}: v2 {x['uptake_v2']:.3f} {'PASS' if x['uptake_v2_pass'] else 'fail'}"
          f" (v1 {x['uptake_v1']:.3f}) non_en_cells {x['non_english_cells']} | coGO {x['coGO']:.3f} cap {x['capture']:.3f}"
          f" Gx {x['G_others']:.2f} | top coGO {x['top']['coGO']} cap {x['top']['capture']} Gx {x['top']['G_others']}"
          f" | effect {x['effect']} | valid {x['valid_rounds']} | reveals {x['reveals']}")
up = sum(x["uptake_v2_pass"] for x in t1)
eff = sum(x["effect"] for x in t1)
both = sum(x["uptake_v2_pass"] and x["effect"] for x in t1)
print(f"  uptake v2 pass {up}/{len(t1)}; v1 pass {sum(x['uptake_v1_pass'] for x in t1)}/{len(t1)}; "
      f"effect (top coGO & Gx>0) {eff}/{len(t1)}; both {both}/{len(t1)}; top coGO {sum(x['top']['coGO'] for x in t1)}; "
      f"Gx>0 {sum((x['G_others'] or 0) > 0 for x in t1)}; capture>=2 rounds {sum((x['capture_rounds'] or 0) >= 2 for x in t1)}")
print("  Type 2 uptake v2 pass (falsification-style):", sum(x["uptake_v2_pass"] for x in by_t[2]), "/", len(by_t[2]))
print("\nRQ0.2 Type 3:")
for x in sorted(by_t[3], key=lambda x: x["game_id"]):
    print(f"  {x['game_id']} {x['focal']}: coGO {x['coGO']:.3f} (pct {x['pct_vs_null']['coGO']:.0f}) cap {x['capture']:.3f} "
          f"(pct {x['pct_vs_null']['capture']:.0f}) Gx {x['G_others']:.2f} (pct {x['pct_vs_null']['G_others']:.0f}) | "
          f"naming {x['msgs_naming_partner']}/{x['focal_msgs']} warm {x['persona_warm_msgs']} | inside null {x['inside_null']}"
          f" | {x['verdict']} | ex: {x['persona_examples'][:1]}")
print("  verdicts:", dict(Counter(x["verdict"] for x in by_t[3])))
print("\nRQ0.2 Type 4b:")
for x in sorted(by_t[4], key=lambda x: x["game_id"]):
    print(f"  {x['game_id']} {x['focal']}: GO {dict((k, round(v, 3)) for k, v in x['go_rate'].items())} | coGO {x['coGO']:.3f}"
          f" (pct {x['pct_vs_null']['coGO']:.0f}) cap {x['capture']:.3f} (pct {x['pct_vs_null']['capture']:.0f}) Gx "
          f"{x['G_others']:.2f} (pct {x['pct_vs_null']['G_others']:.0f}) | top coGO {x['top']['coGO']} | deposit {x['deposit_public']}"
          f" | {x['verdict']}")
print("  verdicts:", dict(Counter(x["verdict"] for x in by_t[4])))
print("  4b games with deposit talk in public:", sum(x["deposit_public"] > 0 for x in by_t[4]), "/", len(by_t[4]),
      "; total mentions", sum(x["deposit_public"] for x in by_t[4]))
print("\nType 2 focal (decoy) vs null:", [(x["game_id"], round(x["coGO"], 3), x["top"]["coGO"]) for x in by_t[2]])
