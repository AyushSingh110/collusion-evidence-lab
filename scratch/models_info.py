import json, sys
from ollama_util import get, post
tags = get("/api/tags")["models"]
out = {}
for m in tags:
    show, _ = post("/api/show", {"model": m["name"]})
    mi = show.get("model_info", {})
    ctx = next((v for k, v in mi.items() if k.endswith(".context_length")), None)
    out[m["name"]] = {"digest": m["digest"], "size_gb": round(m["size"] / 1e9, 2),
                      "params": m["details"].get("parameter_size"), "quant": m["details"].get("quantization_level"),
                      "family": m["details"].get("family"), "trained_ctx": ctx,
                      "default_params": show.get("parameters", "").replace("\n", " | ")[:160]}
    print(m["name"], json.dumps(out[m["name"]]))
json.dump(out, open("models_info.json", "w"), indent=1)
