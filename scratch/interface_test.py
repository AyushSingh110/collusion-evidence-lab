"""Task 01 throwaway: Part 2.2 interface checks against local Ollama (stdlib HTTP only)."""
import json, sys, time
from ollama_util import post, get
import prompts_draft as P

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b"
sysp, userp, schema = P.stage1("J", P.history_block([], "J"))
msgs = [{"role": "system", "content": sysp}, {"role": "user", "content": userp}]
res = {}

def native(seed, temp=1.0, num_ctx=8192, num_predict=400, messages=msgs, fmt=schema["schema"]):
    body, dt = post("/api/chat", {"model": MODEL, "messages": messages, "stream": False, "format": fmt,
                                  "options": {"num_ctx": num_ctx, "num_predict": num_predict, "temperature": temp, "seed": seed},
                                  "keep_alive": "10m"})
    return body, dt

def ps():
    return [{k: m.get(k) for k in ("name", "digest", "size", "size_vram", "context_length")} for m in get("/api/ps")["models"]]

# 1. native + schema, cold load
b, dt = native(123)
res["native_cold"] = {"latency_s": round(dt, 2), "load_s": round(b.get("load_duration", 0) / 1e9, 2),
                      "prompt_tokens": b.get("prompt_eval_count"), "gen_tokens": b.get("eval_count"),
                      "prompt_tok_s": round(b["prompt_eval_count"] / (b["prompt_eval_duration"] / 1e9), 1),
                      "gen_tok_s": round(b["eval_count"] / (b["eval_duration"] / 1e9), 1),
                      "content": b["message"]["content"][:300], "ps": ps()}
try:
    res["native_cold"]["parsed"] = json.loads(b["message"]["content"])
except Exception as e:
    res["native_cold"]["parse_error"] = repr(e)

# 2. seed determinism (same request x3, then a different seed)
outs = [native(123)[0]["message"]["content"] for _ in range(3)]
res["seed_same_x3_identical"] = len(set(outs)) == 1
res["seed_same_contents"] = [o[:120] for o in outs]
res["seed_other_differs"] = native(999)[0]["message"]["content"] != outs[0]
res["seed_temp0_x2_identical"] = len({native(5, temp=0.0)[0]["message"]["content"] for _ in range(2)}) == 1

# 3. OpenAI-compatible endpoint with response_format json_schema
ob, odt = post("/v1/chat/completions", {"model": MODEL, "messages": msgs, "seed": 123, "temperature": 1.0, "max_tokens": 400,
                                        "response_format": {"type": "json_schema", "json_schema": schema}})
oc = ob["choices"][0]["message"]["content"]
res["openai_compat"] = {"latency_s": round(odt, 2), "usage": ob.get("usage"), "content": oc[:300], "ps_after": ps()}
try:
    res["openai_compat"]["parsed"] = json.loads(oc)
except Exception as e:
    res["openai_compat"]["parse_error"] = repr(e)
# does /v1 accept an options.num_ctx override? (non-standard field)
ob2, _ = post("/v1/chat/completions", {"model": MODEL, "messages": msgs, "max_tokens": 50, "options": {"num_ctx": 2048}})
res["openai_compat_options_numctx_ps"] = ps()

# 4. truncation: ~3k-token prompt with num_ctx=2048 -> does Ollama report fewer prompt tokens?
long_user = userp + "\n\nBackground notes:\n" + ("The bar has wooden tables and a small stage. " * 300)
lm = [{"role": "system", "content": sysp}, {"role": "user", "content": long_user}]
b_small, _ = native(1, num_ctx=2048, num_predict=20, messages=lm, fmt=None)
b_big, _ = native(1, num_ctx=8192, num_predict=20, messages=lm, fmt=None)
res["truncation"] = {"prompt_tokens_numctx2048": b_small.get("prompt_eval_count"),
                     "prompt_tokens_numctx8192": b_big.get("prompt_eval_count")}
res["ollama_version"] = get("/api/version")["version"]
json.dump(res, open(f"interface_{MODEL.replace(':', '_')}.json", "w"), indent=1)
print(json.dumps(res, indent=1)[:6000])
