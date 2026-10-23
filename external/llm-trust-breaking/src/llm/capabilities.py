"""Single source of truth for per-model API capabilities.

Each client used to carry its own ``STRUCTURED_OUTPUT_MODELS`` set, and the sets
disagreed with each other: the same model got a JSON schema on one code path and
prompt-based JSON forcing on another, depending on whether a run used the queued
client, the parallel client or the synchronous one.

This project supports any ``response_format``-capable model, routed via the shared
inference config (Nebius default, OpenRouter fallback). Non-OpenAI models are
accepted (with a warning), not rejected. Names here are OpenRouter-qualified; bare
names are qualified before lookup, so ``gpt-4o-mini`` and ``openai/gpt-4o-mini``
resolve alike.
"""
from __future__ import annotations


# OpenAI models that accept the response_format JSON-schema parameter.
STRUCTURED_OUTPUT_MODELS = frozenset({
    "openai/gpt-3.5-turbo",
    "openai/gpt-4",
    "openai/gpt-4-turbo",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1-nano",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "openai/gpt-5-nano",
    "openai/gpt-5-pro",
    "openai/gpt-5.2",
    "openai/gpt-oss-safeguard-20b",
    "openai/gpt-oss-safeguard-120b",
    "openai/o1-mini",
    "openai/o1-preview",
    "openai/o3-mini",
})


def qualify(model: str) -> str:
    """Return the OpenRouter-qualified form of a model name."""
    return model if "/" in model else f"openai/{model}"


def supports_structured_output(model: str) -> bool:
    """Whether this model accepts response_format with a JSON schema."""
    return qualify(model) in STRUCTURED_OUTPUT_MODELS


# Reasoning models reject `temperature`/`seed` and take `reasoning_effort` instead.
# This is about which sampling parameters a request may carry — it says nothing about
# structured output, which is decided by STRUCTURED_OUTPUT_MODELS above.
def is_reasoning_model(model: str) -> bool:
    """Whether this model uses reasoning_effort in place of temperature/seed."""
    return (
        "/o1" in model or "/o3" in model or "/gpt-5" in model
        or "qwen" in model.lower()
        or model.startswith("o1") or model.startswith("o3") or model.startswith("gpt-5")
    )
