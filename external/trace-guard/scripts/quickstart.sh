#!/bin/bash
# TraceGuard Quick Start.
#
# This project runs inside ControlArena's BashArena, which executes every task in a
# Docker container. That makes it the one project in this repository with an
# infrastructure prerequisite, so this script checks each one and STOPS at the first
# that is missing. The smoke test it ends with is deliberately tiny (one monitor, one
# threshold, one side task, 2 samples -- a handful of model calls), but BashArena still
# builds its Docker images on that first run (~15-20 GB, several minutes), and the full
# experiment is 6-8 hours; nothing here should start until the cheap checks pass.
set -euo pipefail
cd "$(dirname "$0")/.."

fail() {
    echo ""
    echo "ERROR: $1"
    echo "       $2"
    exit 1
}

echo "=== TraceGuard Quick Start ==="
echo ""

# Ensure the project venv exists and is active. On a fresh checkout there is no .venv, so bare `python`
# would be the system interpreter (without control-arena) and `uv sync` would fail with
# "No virtual environment found". Create + activate it here so the checks below use the right interpreter.
if [ -z "${VIRTUAL_ENV:-}" ]; then
    [ -d .venv ] || { echo "   creating project venv (uv venv)..."; uv venv \
        || fail "could not create a virtual environment." "Install uv (https://docs.astral.sh/uv/) and re-run."; }
    # shellcheck source=/dev/null
    source .venv/bin/activate
fi

echo "1. Prerequisites"
python -c "import control_arena" 2>/dev/null \
    || fail "control-arena is not installed." "Run: uv sync   (installs the locked inspect-ai + control-arena set, ~1 GB)"
python -c "import inspect_ai" 2>/dev/null \
    || fail "inspect-ai is not installed." "Run: uv sync"
docker info >/dev/null 2>&1 \
    || fail "Docker is not running." "Start Docker (Desktop or daemon) -- BashArena runs every task in a container -- then re-run."
[ -f ../compute.env ] \
    || fail "repo-root compute.env not found." "Run at the repo root: cp compute.env.example compute.env   and put your OPENROUTER_API_KEY in it (see ../COMPUTE.md)."
echo "   control-arena, inspect-ai, Docker, compute.env: OK"

echo ""
echo "2. Model access (seconds -- always before the eval)"
python scripts/test_model_access.py \
    || fail "A configured model did not answer." "Check your key in the repo-root compute.env and the model ids printed above."

echo ""
echo "3. BashArena images build lazily on the first run_eval.py below"
echo "   (ControlArena builds them on demand -- ~15-20 GB and several minutes the first time;"
echo "    there is no separate setup step. Subsequent runs reuse the cached images.)"

echo ""
echo "4. Smoke test: TraceGuard monitor, attack-only, one threshold, one side task, 2 samples"
echo "   (genuinely cheap: a handful of model calls -- NOT the full 168-task default)"
python scripts/run_eval.py --monitor traceguard --attack-only --thresholds 0.5 --limit 2 --side-tasks download_malware

echo ""
echo "=== Quick start complete ==="
echo "Next steps:"
echo "  - Full experiment (6-8 h):  python scripts/run_eval.py --all-monitors --limit 50"
echo "  - Analyze results:          python scripts/analyze_results.py --log-dir logs/"
echo "  - Post-hoc testing:         python scripts/run_posthoc.py --log-dir logs/ --all-monitors"
