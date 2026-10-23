"""
Factory for creating LLM clients.

Model traffic goes through the shared inference config (`poseidon_compute`; Nebius
default, OpenRouter fallback).

Structured output matters here: agent decisions are read back as JSON via
`response_format`, and a model without that support falls through to asking for JSON
inside the prompt, whose failure mode is an empty decision rather than an error. The
factory warns on an unsupported model at startup rather than letting a run silently
finish with unusable data.
"""

from typing import Tuple

# Route provider base_url / key / model through the repo-root shared LLM config.
from poseidon_compute import base_url as _llm_base_url, api_key as _llm_api_key, resolve_model

from src.llm.capabilities import is_reasoning_model, supports_structured_output
from src.llm.providers.openrouter_client import OpenRouterClient
from src.llm.providers.parallel_openrouter_async import AsyncOpenRouterParallelClient


def normalize_model_name(model: str) -> str:
    """
    Normalise a model name for OpenRouter.

    A name that already carries a provider prefix is returned unchanged. A bare
    OpenAI name gains the `openai/` prefix. Anything else is left alone so that
    `require_supported_model` can reject it by name.

    Examples:
        >>> normalize_model_name("gpt-4o-mini")
        'openai/gpt-4o-mini'
        >>> normalize_model_name("openai/gpt-4o")
        'openai/gpt-4o'
        >>> normalize_model_name("claude-3.5-sonnet")
        'claude-3.5-sonnet'
    """
    if "/" in model:
        return model

    lower = model.lower()
    if lower.startswith("gpt-") or lower.startswith("o1") or lower.startswith("o3"):
        return f"openai/{model}"
    return model


def require_supported_model(model: str) -> str:
    """
    Qualify a model name and refuse the ones this project cannot run correctly.

    Returns the OpenRouter-qualified name. Raises ValueError for a non-OpenAI model,
    and warns for an OpenAI model that is not known to accept a JSON schema.
    """
    normalised = normalize_model_name(model)

    if not normalised.startswith("openai/"):
        print(
            f"NOTE: '{model}' is not an OpenAI model. This project needs structured (JSON) output to "
            "read agent decisions; on Nebius/Modal use a model that supports response_format/JSON "
            "(e.g. a Qwen or Llama variant that does). If decisions come back EMPTY at runtime the "
            "trial runner aborts with an error rather than recording unusable data. Proceeding."
        )
        return normalised

    if not supports_structured_output(normalised):
        print(
            f"WARNING: '{normalised}' is not in the structured-output table "
            "(src/llm/capabilities.py). Decisions will be requested as JSON inside the "
            "prompt, and a parse failure yields an EMPTY decision rather than an error. "
            "Check the run output before trusting it."
        )

    return normalised


def create_llm_clients(
    model: str,
    openrouter_api_key: str = None,
    temperature: float = 1.0,
    max_workers: int = 20,
) -> Tuple[object, object]:
    """
    Create the OpenRouter client and its matching parallel client.

    Args:
        model:              Model identifier (normalised and validated here).
        openrouter_api_key: OpenRouter API key.
        temperature:        Sampling temperature.
        max_workers:        Max concurrent requests for the parallel client.

    Returns:
        (llm_client, parallel_client)
    """
    # Default the model id through the shared config (LLM_MODEL override / Nebius mapping).
    model = resolve_model(model)
    normalised = require_supported_model(model)

    # Key and provider endpoint come from the shared compute.env (llm_config); fall back to
    # the key passed in (this project's own .env) if the shared config has none.
    openrouter_api_key = _llm_api_key() or openrouter_api_key
    if not openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Add it to this project's .env "
            "(see .env.example)."
        )

    # llm_config.base_url() returns the provider root (e.g. https://openrouter.ai/api/v1);
    # these clients POST to the chat/completions endpoint under it.
    chat_url = _llm_base_url().rstrip("/") + "/chat/completions"

    # Reasoning models spend much longer before emitting their first token.
    timeout = 300 if is_reasoning_model(normalised) else 120

    print(f"Using provider endpoint {chat_url} with model: {normalised}")
    llm_client = OpenRouterClient(
        api_key=openrouter_api_key,
        model=normalised,
        temperature=temperature,
        timeout=timeout,
        base_url=chat_url,
    )
    parallel_client = AsyncOpenRouterParallelClient(
        api_key=openrouter_api_key,
        max_concurrent=max_workers,
        timeout=timeout,
        base_url=chat_url,
    )
    return llm_client, parallel_client
