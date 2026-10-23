"""Smoke test: can this machine reach the models TraceGuard will use?

Run it before the BashArena smoke test. It loads the repo-root compute.env
(the same provider config run_eval.py uses, via scripts/_provider_shim.py) plus any
per-project .env overrides, and asks each configured model for a one-word reply through
inspect-ai -- the same path the evaluation takes -- so a wrong key or model id fails here
in seconds.

    python scripts/test_model_access.py
    python scripts/test_model_access.py --untrusted-model openrouter/openai/gpt-4o

Replaces the former test_bedrock_claude.py (the intent analyzer no longer needs Bedrock).
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Bridge the repo-root compute.env into the provider config, exactly as run_eval.py does,
# so a key placed there (not just in a local .env) is seen -- the two scripts must agree.
# _provider_shim imports poseidon_compute, which walks up to find and load compute.env.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _provider_shim

# Per-project overrides (e.g. INTENT_MODEL) still come from this project's .env, if present.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_UNTRUSTED = "openrouter/openai/gpt-4o"
DEFAULT_TRUSTED = "openrouter/openai/gpt-4o-mini"


async def probe(label: str, model_str: str) -> bool:
    from inspect_ai.model import get_model

    try:
        model = get_model(model_str)
        output = await model.generate(input="Reply with the single word OK.")
        print(f"  OK    {label:<10} {model_str:<44} -> {output.completion.strip()[:40]!r}")
        return True
    except Exception as exc:  # noqa: BLE001 - we want to report anything at all
        print(f"  FAIL  {label:<10} {model_str:<44} -> {type(exc).__name__}: {str(exc)[:140]}")
        return False


async def main() -> int:
    parser = argparse.ArgumentParser(description="Check that the configured models answer.")
    parser.add_argument("--untrusted-model", default=DEFAULT_UNTRUSTED)
    parser.add_argument("--trusted-model", default=DEFAULT_TRUSTED)
    args = parser.parse_args()

    # Point inspect-ai's provider at the configured endpoint and remap model strings the
    # same way run_eval.py does (openrouter -> unchanged; nebius -> openai/<model>), so this
    # check exercises the real evaluation path. apply() raises if no key is configured.
    try:
        provider = _provider_shim.apply()
    except Exception as exc:  # noqa: BLE001
        print(f"{type(exc).__name__}: {exc}")
        return 1
    args.untrusted_model = _provider_shim.map_model(args.untrusted_model)
    args.trusted_model = _provider_shim.map_model(args.trusted_model)

    if provider == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key or key == "your-openrouter-key-here":
            print("OPENROUTER_API_KEY is not set (or is still the placeholder) in the repo-root "
                  "compute.env. See ../COMPUTE.md.")
            return 1

    targets = [("untrusted", args.untrusted_model), ("trusted", args.trusted_model)]
    intent = os.environ.get("INTENT_MODEL")
    if intent:
        intent = _provider_shim.map_model(intent)
        targets.append(("intent", intent))
    else:
        print("  skip  intent     INTENT_MODEL not set -- intent analysis stays disabled (set it in the repo-root compute.env; see ../compute.env.example)")

    results = await asyncio.gather(*(probe(label, model) for label, model in targets))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
