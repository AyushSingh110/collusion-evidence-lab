"""Task 09c: token counts of alliance_v4 / placebo_v3 with qwen2.5:7b (same nonce-difference method as task 06a /
report 01 §6). Re-measures alliance_v3 as a method check (expected 130)."""
import json, random, sys, urllib.request
from pathlib import Path

d = Path(__file__).resolve().parents[1] / "configs" / "prompts"


def n_tokens(system):
    body = {"model": "qwen2.5:7b", "stream": False, "keep_alive": "5m",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": "ok"}],
            "options": {"num_ctx": 8192, "num_predict": 1, "temperature": 0, "seed": 1}}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read())["prompt_eval_count"]


def count(text):
    nonce = f"[{random.randint(10**8, 10**9)}]"
    return n_tokens(nonce + "\n" + text) - n_tokens(nonce)


out = {}
for name in ("alliance_v3.txt", "alliance_v4.txt", "placebo_v3.txt"):
    text = (d / name).read_text(encoding="utf-8").rstrip("\n").replace("{P}", "T")
    out[name] = count(text)
    print(name, out[name])
print("ratio placebo_v3/alliance_v4 =", round(out["placebo_v3.txt"] / out["alliance_v4.txt"], 4))
json.dump(out, sys.stdout)
print()
