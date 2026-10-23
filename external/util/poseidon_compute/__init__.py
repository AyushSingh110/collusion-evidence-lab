"""Shared compute / inference layer for every experiment in this repo.

Configure once in the repo-root ``compute.env`` (copy ``compute.env.example``), then import what you
need directly — no path hacking, no per-file bootstrap:

    from poseidon_compute import make_client, resolve_model

    client = make_client()                      # OpenAI-compatible client at the configured endpoint
    model  = resolve_model("Qwen/Qwen2.5-7B-Instruct")

Every call routes **Nebius → OpenRouter → Modal → fail loudly**, never silently substituting a
model / provider / key. The ``poseidon-run`` console script wraps a whole command with that routing:

    poseidon-run --model <id> -- <your experiment command>

See the repo-root ``COMPUTE.md`` for the full story.
"""
from .llm_config import (
    make_client,
    resolve_model,
    api_key,
    base_url,
    openrouter_api_key,
    endpoint_kind,
    nebius_serves,
    openrouter_serves,
    config,
    NEBIUS_BASE_URL,
    OPENROUTER_BASE_URL,
)
from .hosted_model import hosted_model, ModelAccessError

__all__ = [
    "make_client",
    "resolve_model",
    "api_key",
    "base_url",
    "openrouter_api_key",
    "endpoint_kind",
    "nebius_serves",
    "openrouter_serves",
    "config",
    "NEBIUS_BASE_URL",
    "OPENROUTER_BASE_URL",
    "hosted_model",
    "ModelAccessError",
]
