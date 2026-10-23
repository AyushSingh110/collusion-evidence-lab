"""Task 01 throwaway: token counts for the v2 alliance/placebo addenda (same nonce method as token_counts.py)."""
import random, sys
from ollama_util import post
import prompts_draft as P

MODEL = sys.argv[1]


def n_tokens(system):
    b, _ = post("/api/chat", {"model": MODEL, "stream": False, "keep_alive": "5m",
                              "messages": [{"role": "system", "content": system}, {"role": "user", "content": "ok"}],
                              "options": {"num_ctx": 8192, "num_predict": 1, "temperature": 0, "seed": 1}})
    return b["prompt_eval_count"]


def count(text):
    nonce = f"[{random.randint(10**8, 10**9)}]"
    return n_tokens(nonce + "\n" + text) - n_tokens(nonce)


for k, v in P.ADDENDUM_V2.items():
    print(f"{MODEL} v2 {k}: {count(v.replace('{P}', 'T'))} tokens, {len(v.replace('{P}', 'T'))} chars")
post("/api/chat", {"model": MODEL, "messages": [], "keep_alive": 0})
