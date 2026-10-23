"""vLLM model server on Modal — an OpenAI-compatible endpoint for experiments Nebius can't serve.

You don't run this directly. `poseidon_compute.hosted_model` runs it ephemerally around an experiment (boots a
model, wires the endpoint into `llm_config`, tears it down):

    poseidon-host --model Qwen/Qwen2.5-7B-Instruct --gpu A10G -- <your experiment command>

SETUP (one-time): `pip install modal && modal setup` (browser auth). Gated models (e.g. Llama) need a
HF token: `modal secret create huggingface HF_TOKEN=hf_...`. Pick a GPU that fits the model: A10G (24GB)
~ up to 8B · A100-40GB ~ up to 32B · H100 for 70B (pass `--gpu` to hosted_model).

Advanced: `modal deploy poseidon_compute.modal_serve` gives a persistent shared endpoint; most teams won't need
it (the ephemeral hosted_model flow is simpler and leaves nothing running). Scaffolding ahead of live
credits — validate once your Modal account is funded.
"""
import os
import subprocess

import modal

# ---- config (override via env at deploy time) ----------------------------------------------------
MODEL = os.environ.get("MODAL_SERVE_MODEL", "Qwen/Qwen2.5-7B-Instruct")  # open by default (no HF gate)
GPU = os.environ.get("MODAL_SERVE_GPU", "A10G")
VLLM_PORT = 8000

app = modal.App("hackathon-serve")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.6.6", "huggingface_hub[hf_transfer]==0.26.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# HF token (for gated models) + optional endpoint API key. Both secrets are optional: if you haven't
# created them, drop the corresponding entry.
_secrets = []
for name in ("huggingface", "modal-serve"):
    try:
        _secrets.append(modal.Secret.from_name(name))
    except Exception:
        print(f"[modal_serve] note: Modal secret '{name}' not found — skipping. "
              f"('huggingface' is needed for GATED models like Llama; 'modal-serve' only to protect "
              f"the endpoint with a key.) Without it, a run that needs it will fail at startup.")


@app.function(
    image=image,
    gpu=GPU,
    timeout=24 * 3600,
    scaledown_window=300,            # spin down after 5 min idle to save credits
    secrets=_secrets,
)
# (for higher throughput on one GPU, add `@modal.concurrent(max_inputs=N)` above web_server)
@modal.web_server(port=VLLM_PORT, startup_timeout=900)
def serve():
    """Launch vLLM's OpenAI-compatible server; Modal proxies it to a public URL."""
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--served-model-name", MODEL,
    ]
    api_key = os.environ.get("MODAL_SERVE_API_KEY")
    if api_key:
        cmd += ["--api-key", api_key]   # clients must send this as their key
    subprocess.Popen(" ".join(cmd), shell=True)
