"""Task 01 throwaway: summarise results/format_<model>.json."""
import json, statistics as st, sys

for model in sys.argv[1:]:
    d = json.load(open(f"results/format_{model.replace(':', '_')}.json"))
    print(f"\n=== {model}")
    for temp in (1.0, 0.7):
        rows = [r for r in d["format"] if r["temp"] == temp]
        ok = sum(r.get("valid", False) for r in rows)
        trunc = sum(r.get("done_reason") == "length" for r in rows)
        print(f"temp {temp}: valid {ok}/{len(rows)}  truncated(length) {trunc}  transport_fail {sum(not r['ok_transport'] for r in rows)}")
    rows = [r for r in d["format"] if r.get("ok_transport") and r.get("load_s", 0) < 5]
    for stage in (1, 2, 3):
        rs = [r for r in rows if r["stage"] == stage]
        print(f"stage {stage}: n={len(rs)} median latency {st.median(r['latency_s'] for r in rs):.1f}s  "
              f"median prompt {st.median(r['prompt_tokens'] for r in rs):.0f} tok  median gen {st.median(r['gen_tokens'] for r in rs):.0f} tok")
    pt = [r["prompt_tokens"] / r["prompt_s"] for r in rows if r.get("prompt_s")]
    gt = [r["gen_tokens"] / r["gen_s"] for r in rows if r.get("gen_s")]
    print(f"prompt tok/s median {st.median(pt):.0f}  gen tok/s median {st.median(gt):.1f}  max gen tokens {max(r['gen_tokens'] for r in rows)}")
    cold = [r for r in d["format"] if r.get("load_s", 0) >= 5]
    print("cold loads:", [(r["load_s"]) for r in cold])
    print("sweep (round: latency s, prompt tok, gen tok):",
          [(r["round"], r.get("latency_s"), r.get("prompt_tokens"), r.get("gen_tokens")) for r in d["latency_sweep"]])
    acts = [r["action"] for r in d["format"] if r.get("valid")]
    print("action mix:", {a: acts.count(a) for a in set(acts)})
