"""Task 01 throwaway: print focal-pair private plans, channel messages and public messages of a mini-game."""
import json, sys

rec = json.load(open(sys.argv[1]))
focal = rec["focal"]
print(f"== {rec['model']} {rec['type']} calls={rec['calls']} failures={rec['failures']}")
for R in rec["rounds"]:
    print(f"\n--- ROUND {R['round']} order={R['order']}")
    for a in focal:
        s1 = R["stage1"][a]
        print(f"  [S1 {a}] plan={s1['intended_action']}: {s1['reasoning'][:260]}")
    for c in R["channel"]:
        print(f"  [CH-{c['exchange']} {c['from']}] {(c['text'] or '')[:260]}")
    for s in R["stage2"]:
        tag = "*" if s["agent"] in focal else " "
        print(f"  [S2{tag}{s['agent']}] {s['stated_action']}: {(s['message'] or '')[:200]}")
    for a in focal:
        print(f"  [S3 {a}] {R['stage3'][a]['choice']}: {R['stage3'][a]['reasoning'][:200]}")
    print("  choices:", {a: R["stage3"][a]["choice"] for a in R["stage3"]}, "payoffs:", R["std_payoffs"])
