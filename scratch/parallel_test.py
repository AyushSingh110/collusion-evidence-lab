"""Task 01 throwaway: throughput with concurrent requests. Usage: parallel_test.py <base_url> <model> <label>"""
import json, random, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import bench

BASE, MODEL, LABEL = sys.argv[1], sys.argv[2], sys.argv[3]
NUM_CTX = 4096
rng = random.Random(11)
reqs = []
for i in range(4):
    (s, u, schema), _ = bench.build_stage(3, bench.P.AGENTS[i], bench.synth_history(6, random.Random(i)), random.Random(i))
    reqs.append({"model": MODEL, "stream": False, "keep_alive": "10m", "format": schema["schema"],
                 "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}],
                 "options": {"num_ctx": NUM_CTX, "num_predict": 350, "temperature": 1.0, "seed": 500 + i}})


def go(p):
    t0 = time.time()
    r = urllib.request.Request(BASE + "/api/chat", data=json.dumps(p).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as f:
        b = json.loads(f.read().decode())
    return {"latency_s": round(time.time() - t0, 2), "gen": b.get("eval_count"), "content": b["message"]["content"]}


go(reqs[0])  # warm-up / load
t0 = time.time(); seq = [go(p) for p in reqs]; t_seq = time.time() - t0
t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    par = list(ex.map(go, reqs))
t_par = time.time() - t0
ps = json.loads(urllib.request.urlopen(BASE + "/api/ps").read().decode())["models"]
res = {"label": LABEL, "model": MODEL, "num_ctx": NUM_CTX, "seq_wall_s": round(t_seq, 1), "par4_wall_s": round(t_par, 1),
       "seq_gen_tokens": sum(r["gen"] for r in seq), "par_gen_tokens": sum(r["gen"] for r in par),
       "same_output_seq_vs_par": [a["content"] == b["content"] for a, b in zip(seq, par)],
       "ps": [{k: m.get(k) for k in ("name", "size", "size_vram", "context_length")} for m in ps]}
print(json.dumps(res))
json.dump(res, open(f"results/parallel_{LABEL}_{MODEL.replace(':', '_')}.json", "w"), indent=1)
