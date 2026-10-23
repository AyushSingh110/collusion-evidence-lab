"""Task 01 throwaway: token counts of Part 4 texts with a model's own tokenizer (via prompt_eval_count).

count(text) = prompt_eval_count(system=NONCE+text) - prompt_eval_count(system=NONCE). A unique nonce per pair
of calls prevents Ollama's prompt cache from hiding tokens. num_predict=1, num_ctx explicit.
"""
import json, random, sys
from ollama_util import post
import prompts_draft as P
import bench

MODEL = sys.argv[1]


def n_tokens(system):
    b, _ = post("/api/chat", {"model": MODEL, "stream": False, "keep_alive": "10m",
                              "messages": [{"role": "system", "content": system}, {"role": "user", "content": "ok"}],
                              "options": {"num_ctx": 8192, "num_predict": 1, "temperature": 0, "seed": 1}})
    return b["prompt_eval_count"]


def count(text):
    nonce = f"[{random.randint(10**8, 10**9)}]"
    return n_tokens(nonce + "\n" + text) - n_tokens(nonce)


texts = {f"addendum_{k}": v.replace("{P}", "T") for k, v in P.ADDENDUM.items()}
texts["collusion_hint"] = P.COLLUSION_HINT
cu, _ = P.channel_prompt("M", "T", 3, "before_announcements", [("T", "Shall we both go again?")])
texts["channel_prompt_A_example"] = cu
rng = random.Random(3)
ann = [{"name": a, "stated_action": "GO", "message": bench.SAMPLE_MSGS[i]} for i, a in enumerate(P.AGENTS)]
cu, _ = P.channel_prompt("M", "T", 3, "before_decisions", [("T", "Go again?"), ("M", "Yes, both go.")], announcements=ann)
texts["channel_prompt_B_example"] = cu
for n in (1, 3, 5, 7):
    texts[f"history_after_{n}_rounds"] = P.history_block(bench.synth_history(n, random.Random(n)), "M")
texts["history_after_7_rounds_4b_private_line"] = P.history_block(bench.synth_history(7, random.Random(7)), "M",
                                                                  private_rule={"home": -8})
res = {k: {"tokens": count(v), "chars": len(v)} for k, v in texts.items()}
res["_texts"] = texts
json.dump(res, open(f"results/tokens_{MODEL.replace(':', '_')}.json", "w"), indent=1)
for k, v in res.items():
    if k != "_texts":
        print(f"{k:42s} {v['tokens']:5d} tokens  {v['chars']:5d} chars")
