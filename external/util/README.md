# poseidon-compute

The shared compute / inference layer every experiment in this repo depends on. It is a **real
installable package** — experiments declare it as a dependency and `import` it directly; there is no
path-hacking or per-file bootstrap anywhere.

```python
from poseidon_compute import make_client, resolve_model

client = make_client()                              # OpenAI-compatible client at the configured endpoint
resp = client.chat.completions.create(
    model=resolve_model("Qwen/Qwen2.5-7B-Instruct"),
    messages=[{"role": "user", "content": "hi"}],
)
```

## What it does

One place (`compute.env` at the repo root) sets your key and optional model; every experiment builds
its client from it. Model calls route **Nebius → OpenRouter → Modal → fail loudly** — a model is never
silently swapped for a default. See [`../COMPUTE.md`](../COMPUTE.md) for the full routing story.

## Public API

| import | what it is |
| --- | --- |
| `make_client(async_=False)` | an `(Async)OpenAI` client pointed at the configured endpoint |
| `resolve_model(id)` | the model id to use (retired pins upgraded to current, announced; else pass-through) |
| `nebius_serves(id)` / `openrouter_serves(id)` | catalog checks |
| `api_key()` / `base_url()` / `openrouter_api_key()` / `endpoint_kind()` / `config()` | endpoint/key introspection |
| `hosted_model(model=..., gpu=...)` | context manager: ephemeral Modal model up for a run, torn down on exit |
| `ModelAccessError` | raised when a gated HF model can't be hosted (actionable message) |

## Console scripts

Installed on your PATH with the package:

- `poseidon-run --model <id> -- <command>` — run a command with that model, routed automatically.
- `poseidon-host --model <id> --gpu <gpu> -- <command>` — run a command with a Modal-hosted model up
  for its duration.

## Install

You normally don't install this by hand — the repo-root `./setup.sh` does it for every experiment. It
is wired into each experiment as an **editable** dependency (`[tool.uv.sources]` for uv projects,
`-e ../util` in `requirements.txt` for the rest), so edits here are picked up live. To install it into
the current environment directly:

```bash
pip install -e util          # or: uv pip install -e util
```
