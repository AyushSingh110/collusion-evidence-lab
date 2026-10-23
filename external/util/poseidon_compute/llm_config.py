"""Central LLM config shared by every project in this repo.

ONE place to set your key and (optionally) a model: the repo-root `compute.env`
(copy `compute.env.example` -> `compute.env`). Every project builds its model client from this,
so you configure once and all ten projects follow.

Inference routing (via `poseidon-run`): **Nebius → OpenRouter → Modal → fail loudly.** Nebius is the
default endpoint (OpenAI-compatible, open models); OpenRouter covers models Nebius doesn't serve, including
closed ones (GPT/Gemini/Claude); Modal (`poseidon_compute.hosted_model`) is the escape hatch for
off-catalog or custom models (and vLLM-level control). Each routes the SAME OpenAI-compatible client at a
different endpoint.

compute.env keys (what participants set):
    NEBIUS_API_KEY        your Nebius AI Studio key               (default inference)
    OPENROUTER_API_KEY    (optional) enables the OpenRouter fallback (catalog + closed models)
    LLM_MODEL             (optional) force one model id everywhere

internal (set automatically by poseidon_compute.hosted_model — participants don't configure these):
    LLM_BASE_URL          a custom OpenAI-compatible endpoint (the temporary Modal model)
    LLM_API_KEY           key for that endpoint

No silent substitution and no default model: an unavailable model reroutes (Modal) or fails loudly
(`poseidon-run`) — it is never quietly swapped for an unrelated *default*. The one exception is an explicit,
ANNOUNCED upgrade of a retired model pin to its current same-lineage version (e.g. a long-gone
claude-3.5-sonnet -> the current Sonnet); that preserves the requested model's lineage and is printed at
runtime, so it is not a default fallthrough.

Public API:
    make_client(async_=False)        -> an (Async)OpenAI client pointed at the configured endpoint
    resolve_model(requested)         -> the model id to use (retired pins upgraded to current, announced)
    nebius_serves(model)             -> True / False / None (catalog check)
    openrouter_serves(model)         -> the OpenRouter id serving `model`, or None
    base_url(), api_key(), openrouter_api_key(), endpoint_kind(), config()
"""
import os
import functools
from pathlib import Path

NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Retired model pins -> their current same-lineage equivalent. These pins name model versions no provider
# still serves, so the only options are the current version of the same model family or "can't run."
# resolve_model applies this upgrade and prints it at runtime; it preserves the requested model's lineage
# and never swaps in an unrelated model.
_RETIRED_MODEL_UPGRADES = {
    "anthropic/claude-3.5-sonnet": "anthropic/claude-sonnet-4.5",
    "anthropic/claude-3.7-sonnet": "anthropic/claude-sonnet-4.5",
    "anthropic/claude-3.5-haiku":  "anthropic/claude-haiku-4.5",
    "openai/o1-mini":              "openai/o4-mini",
}
_announced_upgrades = set()  # so we print each upgrade once, not per call

# Cross-provider same-lineage aliases, applied ONLY when routing to OpenRouter (never on Nebius).
# A model Nebius serves under its Hugging Face id may be absent from OpenRouter, which instead carries
# a current same-lineage snapshot. Mapping HF-id -> the OpenRouter id lets an OpenRouter-only user run
# the intended model family instead of a hard 400. This is the same "explicit, announced version upgrade"
# exception used above (printed once), NOT a silent default swap — and it does not affect Nebius routing,
# where the exact requested id is used.
_OPENROUTER_ALIASES = {
    # Ministral-8B-Instruct-2410 (on Nebius) is not on OpenRouter; OpenRouter carries the current
    # Ministral 8B snapshot (2512). Used by llm-agent-collusion-2's `small`/`large` rosters.
    "mistralai/Ministral-8B-Instruct-2410": "mistralai/ministral-8b-2512",
}
_announced_or_aliases = set()
_announced_forced = set()  # announce an LLM_MODEL override of a different requested id once per id


def _find_root_env():
    """Walk up from this file and the CWD to find the repo-root compute.env."""
    for start in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (start, *start.parents):
            f = p / "compute.env"
            if f.exists():
                return f
    return None


_loaded_env_file = None  # cached once a compute.env is found + applied; "not found" is NOT cached


def _load():
    """Load compute.env into os.environ (without overriding anything already set)."""
    global _loaded_env_file
    if _loaded_env_file is not None:
        return _loaded_env_file
    f = _find_root_env()
    if f is None:
        return None  # not found from here — don't cache; a later call (e.g. after a chdir) can still find it
    try:
        from dotenv import dotenv_values
        values = dotenv_values(f)
    except Exception:
        values = {}
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    for k, v in values.items():
        if v is not None and k not in os.environ:
            os.environ[k] = v
    _loaded_env_file = f
    return f


def endpoint_kind():
    """Which endpoint make_client() will use, by precedence:
    'custom'    — LLM_BASE_URL is set (e.g. poseidon_compute.run routing or a Modal-hosted model);
    'nebius'    — NEBIUS_API_KEY is set (the default provider);
    'openrouter'— only OPENROUTER_API_KEY is set (fall back to OpenRouter directly);
    'nebius'    — nothing set (api_key() will then fail loudly)."""
    _load()
    if os.environ.get("LLM_BASE_URL"):
        return "custom"
    if os.environ.get("NEBIUS_API_KEY"):
        return "nebius"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    return "nebius"


def base_url():
    _load()
    if os.environ.get("LLM_BASE_URL"):
        return os.environ["LLM_BASE_URL"]
    # No Nebius key but an OpenRouter key -> talk to OpenRouter directly (so native commands and
    # notebooks work with only an OpenRouter key, not just poseidon_compute.run).
    if not os.environ.get("NEBIUS_API_KEY") and os.environ.get("OPENROUTER_API_KEY"):
        return OPENROUTER_BASE_URL
    return NEBIUS_BASE_URL


def api_key():
    _load()
    # Pick the key that matches the endpoint base_url() selected (see endpoint_kind()).
    if os.environ.get("LLM_BASE_URL"):
        # Custom endpoint (e.g. a Modal-hosted model): use ONLY its own key. Do NOT fall back to the
        # Nebius/OpenRouter keys — that would send your provider key as the bearer to a third-party
        # endpoint. A keyless endpoint still needs a non-empty placeholder for the OpenAI client.
        key = os.environ.get("LLM_API_KEY") or "EMPTY"
    elif os.environ.get("NEBIUS_API_KEY"):
        key = os.environ.get("NEBIUS_API_KEY")
    elif os.environ.get("OPENROUTER_API_KEY"):
        key = os.environ.get("OPENROUTER_API_KEY")
    else:
        key = os.environ.get("LLM_API_KEY")
    if not key:
        raise RuntimeError(
            "No inference API key set. Put NEBIUS_API_KEY (or OPENROUTER_API_KEY) in compute.env "
            "(copy compute.env.example -> compute.env). "
            "(For a Modal-hosted model, poseidon_compute.hosted_model sets LLM_API_KEY for you.)"
        )
    return key


def resolve_model(requested, translate_openrouter=True):
    """The model id to use. `LLM_MODEL` overrides everything; otherwise the requested id passes through.
    The ONLY rewriting is an explicit, announced upgrade of a RETIRED pin to its current same-lineage
    version (see _RETIRED_MODEL_UPGRADES) — the requested model is never silently swapped for an unrelated
    *default*, and there is no default fallback: an unavailable id reroutes (Modal) or fails loudly
    (poseidon_compute.run). Ids are written in Nebius / Hugging Face casing throughout."""
    _load()
    forced = os.environ.get("LLM_MODEL")
    if forced and forced != requested and requested not in _announced_forced:
        print(
            f"[llm_config] NOTE: LLM_MODEL='{forced}' overrides the requested model '{requested}'. "
            f"LLM_MODEL forces ONE model for EVERY role — in multi-model experiments (e.g. trace-guard "
            f"trusted vs untrusted, llm-agent-collusion(-2) rosters/judges/overseers) every role collapses "
            f"to '{forced}', which invalidates the comparison. Unset LLM_MODEL and pass per-role models to "
            f"run the intended design.",
            flush=True,
        )
        _announced_forced.add(requested)
    model = forced if forced else requested
    upgraded = _RETIRED_MODEL_UPGRADES.get(model)
    if upgraded and upgraded != model:
        if model not in _announced_upgrades:
            print(f"[llm_config] NOTE: '{model}' is retired; using its current equivalent "
                  f"'{upgraded}' (explicit version upgrade, not a default substitution).", flush=True)
            _announced_upgrades.add(model)
        model = upgraded
    # Translate to OpenRouter's casing only for DIRECT client use on an OpenRouter-only endpoint, so a
    # Hugging-Face-cased id resolves there. poseidon_compute.run does its own Nebius-vs-OpenRouter catalog
    # lookup and passes translate_openrouter=False, so those checks see the id in its original casing.
    # No-op if the id is already an OpenRouter id or not in the catalog (then it passes through).
    if translate_openrouter and endpoint_kind() == "openrouter":
        return openrouter_serves(model) or model
    return model


_nebius_cat = None  # success-only cache: an absent key or a failed fetch is NOT cached (so it can retry)


def _nebius_catalog():
    """Set of model ids Nebius currently serves (GET /v1/models), or None if it can't be fetched."""
    global _nebius_cat
    if _nebius_cat is not None:
        return _nebius_cat
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        return None  # no Nebius key configured — can't (and needn't) check; expected, not cached
    import urllib.request
    import json
    try:
        req = urllib.request.Request(NEBIUS_BASE_URL.rstrip("/") + "/models")
        req.add_header("Authorization", f"Bearer {key}")
        with urllib.request.urlopen(req, timeout=15) as r:
            _nebius_cat = {m.get("id") for m in json.load(r).get("data", [])}
            return _nebius_cat
    except Exception as e:
        # a key IS set but the fetch failed (bad key, network, Nebius down) — surface the reason.
        print(f"[llm_config] WARNING: couldn't fetch the Nebius model catalog "
              f"({type(e).__name__}: {e}) — can't verify model availability.", flush=True)
        return None


def nebius_serves(model):
    """True / False if Nebius serves `model`; None if the catalog couldn't be checked."""
    _load()
    cat = _nebius_catalog()
    return None if cat is None else (model in cat)


def openrouter_api_key():
    _load()
    return os.environ.get("OPENROUTER_API_KEY")


def _norm_model(s):
    """Normalize a model id to its bare name for cross-provider matching: drop the provider prefix,
    lowercase, strip non-alphanumerics. 'meta-llama/Llama-3.3-70B-Instruct' -> 'llama3370binstruct'."""
    import re
    return re.sub(r"[^a-z0-9]", "", s.split("/")[-1].lower())


_openrouter_cat = None  # success-only cache (a failed fetch is NOT cached, so it can retry)


def _openrouter_catalog():
    """Map normalized-model-name -> real OpenRouter id. Listing is PUBLIC (no key needed to check);
    a key is only needed to actually call the model. None if the catalog couldn't be fetched."""
    global _openrouter_cat
    if _openrouter_cat is not None:
        return _openrouter_cat
    import urllib.request
    import json
    try:
        req = urllib.request.Request(OPENROUTER_BASE_URL.rstrip("/") + "/models")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r).get("data", [])
        out = {}
        for m in data:
            mid = m.get("id") or ""
            if mid and not mid.endswith(":batch") and not mid.startswith("~"):
                out.setdefault(_norm_model(mid), mid)
        _openrouter_cat = out
        return out
    except Exception as e:
        print(f"[llm_config] WARNING: couldn't fetch the OpenRouter catalog "
              f"({type(e).__name__}: {e}) — can't verify OpenRouter availability.", flush=True)
        return None


def openrouter_serves(model):
    """The OpenRouter id serving `model` (matched by normalized name), or None if not in the catalog /
    the catalog couldn't be fetched. Returns the OR-cased id so the caller routes with the right spelling
    (Nebius uses Hugging Face casing; OpenRouter uses its own) — no OR-cased ids live in project code."""
    _load()
    cat = _openrouter_catalog()
    if cat is None:
        return None
    hit = cat.get(_norm_model(model))
    if hit:
        return hit
    # Not found by normalized name — try an explicit same-lineage OpenRouter alias (announced once).
    alias = _OPENROUTER_ALIASES.get(model)
    if alias:
        aliased = cat.get(_norm_model(alias))
        if aliased:
            if model not in _announced_or_aliases:
                print(f"[llm_config] NOTE: '{model}' isn't served by OpenRouter; using its current "
                      f"same-lineage snapshot there, '{aliased}' (explicit version upgrade, not a default "
                      f"substitution; Nebius still uses the exact id).", flush=True)
                _announced_or_aliases.add(model)
            return aliased
    return None


def config():
    _load()  # diagnostic view — checks the key without raising, unlike api_key()
    has_key = bool(os.environ.get("LLM_API_KEY") or os.environ.get("NEBIUS_API_KEY")
                   or os.environ.get("OPENROUTER_API_KEY"))
    return {"endpoint": endpoint_kind(), "base_url": base_url(),
            "has_key": has_key, "has_openrouter_key": bool(os.environ.get("OPENROUTER_API_KEY")),
            "forced_model": os.environ.get("LLM_MODEL")}


def make_client(async_=False, **kwargs):
    """Construct an (Async)OpenAI client for the configured endpoint (Nebius or OpenRouter)."""
    from openai import OpenAI, AsyncOpenAI
    cls = AsyncOpenAI if async_ else OpenAI
    return cls(base_url=base_url(), api_key=api_key(), **kwargs)
