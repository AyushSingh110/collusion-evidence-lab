"""Run an experiment with a chosen model, routing inference to where that model actually exists —
and NEVER silently swapping in a different (default) model:

  * Nebius serves the model                          -> run on Nebius
  * else OpenRouter serves it (and a key is set)     -> run on OpenRouter (instant; incl. closed models
                                                        like GPT/Gemini/Claude that Nebius can't host)
  * else it's open-weight                            -> host it on Modal for this run, tear down on exit
  * open-weight but GATED on HF without access        -> FAIL LOUDLY with the model's HF access page + the
                                                        `modal secret create huggingface ...` fix
  * closed model served by no provider               -> FAIL LOUDLY (pick an available model)

Identification is a catalog lookup: `nebius_serves()` (GET Nebius /models) and `openrouter_serves()`
(GET OpenRouter /models, public). Retired model pins are upgraded to their current version first
(resolve_model), announced — see llm_config.

    poseidon-run --model <id> -- <experiment command>          # console script (after setup)
    python -m poseidon_compute.run --model <id> -- <command>    # equivalent

e.g.
    poseidon-run --model Qwen/Qwen2.5-7B-Instruct -- \
        bash -c "cd colosseum && uv run python -m experiments.collusion.run --config ..."
"""
import os
import sys
import argparse
import subprocess

from . import llm_config

# Closed / provider-only families we can't self-host on Modal (vLLM serves open weights only).
_CLOSED_PREFIXES = ("openai/", "gpt-", "o1", "o3", "o4", "gemini", "google/", "anthropic/", "claude")


def _self_hostable(model_id):
    m = model_id.lower()
    return not any(m.startswith(p) for p in _CLOSED_PREFIXES)


def _run(cmd, **env_overrides):
    env = {**os.environ, **{k: v for k, v in env_overrides.items() if v is not None}}
    sys.exit(subprocess.run(cmd, env=env).returncode)


def _run_nebius(model, cmd, confirmed=True):
    msg = (f"Nebius serves '{model}' — running on Nebius." if confirmed
           else f"Running '{model}' on Nebius (unverified — it will fail loudly if not served).")
    print(f"[run] {msg}", flush=True)
    _run(cmd, LLM_MODEL=model)


def _run_openrouter(or_id, cmd):
    print(f"[run] Not on Nebius — '{or_id}' is on OpenRouter. Running there.", flush=True)
    _run(cmd, LLM_BASE_URL=llm_config.OPENROUTER_BASE_URL,
         LLM_API_KEY=llm_config.openrouter_api_key(), LLM_MODEL=or_id)


def _run_modal(model, gpu, cmd):
    print(f"[run] Not on Nebius or OpenRouter — hosting '{model}' on Modal for this run, then tearing "
          f"it down.", flush=True)
    from . import hosted_model
    try:
        with hosted_model.hosted_model(model=model, gpu=gpu):
            sys.exit(subprocess.run(cmd, env=os.environ).returncode)
    except hosted_model.ModelAccessError as e:
        sys.exit(f"[run] ERROR: {e}")  # gated on HF without access — actionable message, no traceback


def main():
    ap = argparse.ArgumentParser(
        description="Run an experiment, routing its model Nebius -> OpenRouter -> Modal (never substituted).")
    ap.add_argument("--model", required=True, help="exact model id you want to run")
    ap.add_argument("--gpu", default=None, help="Modal GPU if it has to self-host, e.g. A10G / A100-40GB / H100")
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="the experiment command, after `--`")
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        ap.error("provide a command after `--`, e.g.  -- bash -c 'cd proj && python ...'")

    # retired pins upgraded (announced); translate_openrouter=False so the catalog lookups below see the
    # id in its original casing — run.py does its own Nebius-vs-OpenRouter routing. Never a default swap.
    model = llm_config.resolve_model(args.model, translate_openrouter=False)
    nb = llm_config.nebius_serves(model)          # True / False / None

    # 1. Nebius serves it.
    if nb is True:
        _run_nebius(model, cmd)

    # 2. OpenRouter serves it (public catalog check; needs a key only to actually call).
    or_id = llm_config.openrouter_serves(model)
    if or_id:
        if llm_config.openrouter_api_key():
            _run_openrouter(or_id, cmd)
        # On OpenRouter but no key:
        if nb is None:
            print("[run] WARNING: couldn't verify Nebius and OPENROUTER_API_KEY isn't set — trying "
                  "Nebius; it will fail loudly if the model isn't served.", flush=True)
            _run_nebius(model, cmd, confirmed=False)
        sys.exit(f"[run] ERROR: '{model}' isn't served by Nebius but IS on OpenRouter (as '{or_id}'). "
                 f"Set OPENROUTER_API_KEY in compute.env to use it, or pick a Nebius model. "
                 f"Not substituting another model.")

    # 3. Not on OpenRouter — open weights can be hosted on Modal.
    if _self_hostable(model):
        _run_modal(model, args.gpu, cmd)

    # 4. Closed model served by nobody.
    if nb is None:
        print("[run] WARNING: couldn't verify the Nebius catalog (check NEBIUS_API_KEY / network). "
              "Trying Nebius; it will fail loudly if the model isn't served.", flush=True)
        _run_nebius(model, cmd, confirmed=False)
    sys.exit(f"[run] ERROR: '{model}' is a closed/proprietary model served by neither Nebius nor "
             f"OpenRouter, and it has no open weights to self-host on Modal. Pick an available model. "
             f"Not substituting another model.")


if __name__ == "__main__":
    main()
