"""Run any starter-repo project on Modal (serverless compute) — one generic runner for all 10.

Why: offload long / parallel runs from your laptop, or use a GPU for the optional `[gpu]` parts.
Your inference provider is still chosen by the project's own `.env` / flags (OpenRouter or Nebius);
Modal just runs the command in the cloud and streams the output back.

--------------------------------------------------------------------------------------------------
ONE-TIME SETUP
    pip install modal
    modal setup                       # authenticate + redeem your hackathon credits (link in Slack/Luma)
    modal secret create hackathon-keys \
        OPENROUTER_API_KEY=sk-or-... \
        NEBIUS_API_KEY=... \
        OPENROUTER_BASE_URL=https://api.studio.nebius.com/v1   # include only if routing via Nebius

USAGE
    # CPU (default):
    modal run modal_run.py --project llm-cartel \
        --cmd "uv run python run_game.py --models openai/gpt-4.1-mini --rounds 30"

    # pip-based project:
    modal run modal_run.py --project llm-agent-collusion-2 \
        --cmd "python -m cleanup_llm.games.tournament --games 1 --steps 5 --out runs/smoke --roster small"

    # GPU (optional [gpu] extras, e.g. llm-cartel steering):
    modal run modal_run.py --project llm-cartel --gpu a10g \
        --cmd "uv run python steering/<script>.py"

The runner uploads the chosen project folder, installs its deps (`uv sync` if it has a
pyproject.toml, else `pip install -r requirements.txt`), injects your `hackathon-keys` secret as
env vars, runs your command in the project dir, and returns the exit code.

NOTE (scaffolding): written ahead of live hackathon credits; validate once your Modal account is
funded. `focal-points` and `trace-guard` need Docker for parts of their pipeline — those parts do
not map onto this basic runner; use their CPU/OpenRouter path instead.
"""
import os

import modal

app = modal.App("hackathon-runner")

# Repo root = parent of this util/ dir, so paths work regardless of where `modal run` is invoked.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The same repo-root compute.env that configures local runs also drives cloud runs: if present it is
# injected as the container's env (LLM_PROVIDER + keys); otherwise fall back to a named Modal secret.
SECRET = (
    modal.Secret.from_dotenv(path=ROOT, filename="compute.env")
    if os.path.exists(os.path.join(ROOT, "compute.env"))
    else modal.Secret.from_name("hackathon-keys")
)

# One image serves every project: the project's own deps are installed at runtime (first call is
# slower; re-runs reuse the cached upload). uv handles the pyproject projects; pip the rest.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "curl", "build-essential")
    .pip_install("uv")
    # upload the repo so any --project is available; skip heavy/irrelevant dirs to keep it fast.
    .add_local_dir(
        ROOT,
        remote_path="/repo",
        ignore=[
            ".git", "**/.git", "**/.venv", "**/__pycache__", "**/node_modules",
            "**/*.tar.gz", "**/*.pt", "**/*.safetensors",
            "compute.env",  # keys travel via the Modal Secret, never baked into the image
        ],
    )
)

REPO = "/repo"


def _install_cmd(proj: str) -> str:
    import os
    if os.path.exists(os.path.join(proj, "pyproject.toml")):
        return "uv sync"
    if os.path.exists(os.path.join(proj, "requirements.txt")):
        return "pip install -r requirements.txt"
    return "true"  # nothing to install


@app.function(
    image=image,
    timeout=3600,
    secrets=[SECRET],
)
def run_project(project: str, cmd: str) -> int:
    """Install the project's deps, then run `cmd` inside the project dir. Output streams live."""
    import os
    import subprocess
    proj = os.path.join(REPO, project)
    if not os.path.isdir(proj):
        raise SystemExit(f"[modal_run] no such project folder: {project!r} (in {REPO})")

    install = _install_cmd(proj)
    print(f"[modal_run] project={project}\n[modal_run] install: {install}\n[modal_run] cmd: {cmd}", flush=True)
    if install != "true":
        subprocess.run(install, cwd=proj, shell=True, check=True)
    result = subprocess.run(cmd, cwd=proj, shell=True)
    print(f"[modal_run] exit code: {result.returncode}", flush=True)
    return result.returncode


@app.local_entrypoint()
def main(project: str, cmd: str, gpu: str = ""):
    """CLI entrypoint. --gpu is optional (e.g. 't4', 'a10g', 'a100'); omit for CPU."""
    fn = run_project.with_options(gpu=gpu) if gpu else run_project
    code = fn.remote(project, cmd)
    if code != 0:
        raise SystemExit(code)
