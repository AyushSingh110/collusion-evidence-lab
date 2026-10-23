"""Bridge the repo-root compute.env into inspect-ai's provider config.

inspect-ai selects a provider from the PREFIX of a model string and reads that provider's creds from
provider-specific env vars. Inference here is always our OpenAI-compatible endpoint (Nebius or OpenRouter,
or a Modal-hosted model when poseidon_compute.hosted_model is active), so we point inspect-ai's built-in
``openai/`` provider at it (OPENAI_BASE_URL / OPENAI_API_KEY) and rewrite model strings to
``openai/<model>``.

No model is ever substituted: `map_model` only normalizes same-model id-spelling (via
llm_config.resolve_model); an unavailable model fails loudly at the API call. Set `LLM_MODEL` (or the
project's INTENT_MODEL / INSPECT_EVAL_MODEL) to an open model Nebius serves, or host it with
`poseidon-run`.

Call ``apply()`` once at startup; call ``map_model(s)`` on each inspect-ai model string.
"""
import os

from poseidon_compute import llm_config


def apply() -> str:
    """Point inspect-ai's openai provider at the configured endpoint. Returns the endpoint kind.
    Raises (via llm_config.api_key()) if no key is configured — fail loudly, don't run keyless."""
    os.environ["OPENAI_BASE_URL"] = llm_config.base_url()
    os.environ["OPENAI_API_KEY"] = llm_config.api_key()
    return llm_config.endpoint_kind()


def map_model(model_str):
    """Rewrite an inspect-ai model string to ``openai/<model>`` for our endpoint. Strips any leading
    provider prefix to recover the bare model id, normalizes same-model spelling (no substitution),
    and re-prefixes. `LLM_MODEL`, if set, wins (via resolve_model)."""
    if model_str is None:
        return None
    m = model_str
    for prefix in ("openrouter/", "openai/"):
        if m.startswith(prefix):
            m = m[len(prefix):]
    return "openai/" + llm_config.resolve_model(m)
