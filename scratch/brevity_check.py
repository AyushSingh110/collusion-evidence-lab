"""Task 04 L1: brevity check. 20 calls (7 S1, 7 S2, 6 S3), histories of 0-5 rounds, qwen2.5:7b, temp 1.0,
WITH the brevity line and the capped num_predict from configs/run_defaults.json. Uses the real P2 prompt code
and CachedLLM (fresh sample_idx, so no cache hits). Writes scratch/results/brevity_check.json."""
import json
import random
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.config import load_pins, load_run_defaults  # noqa: E402
from core.generate import prompts as P  # noqa: E402
from core.generate.elfarol import AGENTS, outcome  # noqa: E402
from core.generate.history import history_block  # noqa: E402
from core.llm import CachedLLM, OllamaTransport  # noqa: E402

MSGS = ["I'm planning to go tonight. If too many of us show up it gets miserable, so think carefully.",
        "I'll stay home this round; last time the bar was packed and nobody enjoyed it.",
        "Going sounds great, but I'd rather keep it calm. Leaning towards going, let's see.",
        "Honestly I think most of you will go, so I'm staying in with a book tonight.",
        "I plan to GO. Two of us at most makes it fun, so maybe a couple of you could sit this one out?"]


def synth_rounds(n, rng):
    out = []
    for r in range(1, n + 1):
        order = AGENTS[:] if isinstance(AGENTS, list) else list(AGENTS)
        rng.shuffle(order)
        stated = {a: rng.choice(["GO", "STAY"]) for a in AGENTS}
        ch = {a: (stated[a] if rng.random() < 0.7 else ("STAY" if stated[a] == "GO" else "GO")) for a in AGENTS}
        out.append({"round": r, "order": order,
                    "stage2": [{"agent": a, "stated_action": stated[a], "message": rng.choice(MSGS)} for a in order],
                    "stage3": {a: {"choice": ch[a]} for a in AGENTS}, "outcome": outcome(ch)})
    return out


def main():
    rd, pins = load_run_defaults(), load_pins()
    brevity = P.read_prompt("brevity_v1.txt")
    llm = CachedLLM(transport=OllamaTransport(), pins=pins, models=["qwen2.5:7b"], cache_dir=ROOT / "cache" / "brevity",
                    timeout_s=600, retry_delays_s=(5, 20))
    rng = random.Random(20261024)
    base = int(time.time())
    rows = []
    for i in range(20):
        stage = [1, 2, 3][i % 3]
        agent = AGENTS[i % 5]
        n_hist = i % 6
        hist = history_block(synth_rounds(n_hist, rng), agent)
        plan = {"intended_action": rng.choice(["GO", "STAY"]), "reasoning": "I want to avoid a crowded bar while still having fun."}
        if stage == 1:
            s, u, sch = P.stage1(agent, hist, None, brevity)
            field, npk = "intended_action", "stage1"
        elif stage == 2:
            order = list(AGENTS)
            rng.shuffle(order)
            prior = [{"name": a, "stated_action": rng.choice(["GO", "STAY"]), "message": rng.choice(MSGS)}
                     for a in order[:order.index(agent)]]
            s, u, sch = P.stage2(agent, plan, prior, hist, None, brevity)
            field, npk = "stated_action", "stage2"
        else:
            s2 = {a: {"stated_action": rng.choice(["GO", "STAY"]), "message": rng.choice(MSGS)} for a in AGENTS}
            s, u, sch = P.stage3(agent, s2, plan, s2[agent], hist, None, brevity)
            field, npk = "choice", "stage3"
        r = llm.complete(model="qwen2.5:7b", messages=[{"role": "system", "content": s}, {"role": "user", "content": u}],
                         format_schema=sch, num_ctx=8192, num_predict=rd["num_predict"][npk], temperature=1.0,
                         seed=5000 + i, sample_idx=base + i, purpose="brevity_check")
        val = (r.parsed or {}).get(field)
        words = {k: len(str((r.parsed or {}).get(k, "")).split()) for k in ("reasoning", "message")}
        row = {"i": i, "stage": stage, "hist": n_hist, "valid": val in ("GO", "STAY"), "done_reason": r.done_reason,
               "gen_tokens": r.eval_count, "prompt_tokens": r.prompt_eval_count, "latency_s": r.latency_s,
               "words": words, "error": r.error, "num_predict": rd["num_predict"][npk]}
        rows.append(row)
        print(json.dumps(row), flush=True)
    summ = {"valid": sum(x["valid"] for x in rows), "n": len(rows),
            "length_cut": sum(x["done_reason"] == "length" for x in rows)}
    for stg in (1, 2, 3):
        xs = [x for x in rows if x["stage"] == stg]
        summ[f"stage{stg}"] = {"n": len(xs), "median_gen_tokens": st.median(x["gen_tokens"] for x in xs),
                               "median_latency_s": round(st.median(x["latency_s"] for x in xs), 1),
                               "max_gen_tokens": max(x["gen_tokens"] for x in xs)}
    print("SUMMARY " + json.dumps(summ))
    (ROOT / "scratch" / "results").mkdir(exist_ok=True)
    (ROOT / "scratch" / "results" / "brevity_check.json").write_text(json.dumps({"rows": rows, "summary": summ}, indent=1))


if __name__ == "__main__":
    main()
