#!/usr/bin/env bash
#
# One-shot setup for every experiment in this repo.
#
# Installs the shared compute layer (poseidon_compute, in ./util) and sets up each experiment's
# environment, so every experiment can `from poseidon_compute import ...` and route inference through
# the one shared `compute.env`.
#
#   ./setup.sh                 # set up ALL experiments
#   ./setup.sh focal-points    # set up only the named experiment(s)
#
# Every experiment is a uv project: `uv sync` installs its deps plus the shared poseidon-compute
# (wired via [tool.uv.sources] -> ../util). uv is the one dependency manager; install it from
# https://docs.astral.sh/uv/ (it also fetches the exact Python each project needs).
#
# Nothing here needs a GPU or any key — it only installs. Put your keys in compute.env afterwards.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

bold=$(printf '\033[1m'); green=$(printf '\033[32m'); red=$(printf '\033[31m')
yellow=$(printf '\033[33m'); dim=$(printf '\033[2m'); rst=$(printf '\033[0m')
ok()   { printf "  ${green}✅ %s${rst}\n" "$*"; }
bad()  { printf "  ${red}❌ %s${rst}\n" "$*"; }
warn() { printf "  ${yellow}⚠  %s${rst}\n" "$*"; }
info() { printf "  ${dim}%s${rst}\n" "$*"; }

PASS=(); FAIL=()

# --- prerequisites --------------------------------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

if ! have uv; then
  bad "uv not found — this repo uses uv for every experiment."
  info "Install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh    (then re-run ./setup.sh)"
  exit 1
fi

# --- compute.env ----------------------------------------------------------------------------------
if [ ! -f "$ROOT/compute.env" ]; then
  if [ -f "$ROOT/compute.env.example" ]; then
    cp "$ROOT/compute.env.example" "$ROOT/compute.env"
    warn "Created compute.env from compute.env.example — open it and add your NEBIUS_API_KEY and/or OPENROUTER_API_KEY."
  else
    warn "No compute.env (and no example to copy). Create one with NEBIUS_API_KEY / OPENROUTER_API_KEY before running experiments."
  fi
else
  ok "compute.env present"
fi

# --- shared package into a repo-root venv (gives you the `poseidon-run` entry point) ---------------
printf "\n${bold}Shared compute layer (poseidon_compute)${rst}\n"
if uv venv "$ROOT/.venv" >/dev/null 2>&1 && uv pip install --python "$ROOT/.venv" -e "$ROOT/util" >/dev/null 2>&1; then
  ok "installed into ./.venv  —  run the entry point with:  ./.venv/bin/poseidon-run --model <id> -- <cmd>"
else
  bad "failed to install poseidon-compute into ./.venv"; FAIL+=("poseidon-compute (root .venv)")
fi

# --- discover experiments -------------------------------------------------------------------------
# An experiment is a direct subdir with a pyproject.toml (every experiment is a uv project), excluding util.
discover() {
  for d in */; do
    d="${d%/}"
    [ "$d" = "util" ] && continue
    if [ -f "$d/pyproject.toml" ]; then echo "$d"; fi
  done
}

if [ "$#" -gt 0 ]; then
  EXPERIMENTS=("$@")
else
  EXPERIMENTS=()
  while IFS= read -r _line; do EXPERIMENTS+=("$_line"); done < <(discover)
fi

setup_one() {
  local d="$1"
  if [ ! -d "$d" ]; then bad "$d — no such directory"; FAIL+=("$d"); return; fi
  printf "\n${bold}%s${rst}\n" "$d"
  if [ -f "$d/pyproject.toml" ]; then
    if ( cd "$d" && uv sync ); then ok "$d — uv sync"; PASS+=("$d"); else bad "$d — uv sync failed"; FAIL+=("$d"); fi
  else
    warn "$d — no pyproject.toml; nothing to do"
  fi
}

for d in "${EXPERIMENTS[@]}"; do setup_one "$d"; done

# --- summary --------------------------------------------------------------------------------------
printf "\n${bold}Summary${rst}\n"
printf "  ${green}%d ok${rst}" "${#PASS[@]}"; [ "${#FAIL[@]}" -gt 0 ] && printf "   ${red}%d failed${rst}" "${#FAIL[@]}"; printf "\n"
if [ "${#FAIL[@]}" -gt 0 ]; then
  for f in "${FAIL[@]}"; do info "failed: $f"; done
  printf "\n${yellow}Some setups failed — see the logs above.${rst}\n"
  exit 1
fi
printf "\n${green}All set.${rst} Put your keys in ${bold}compute.env${rst}, then run any experiment (see its README).\n"
