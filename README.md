# collusion-evidence-lab

A 3-day research hackathon project on **detecting and auditing collusion between LLM agents**.

- **Study 2.2 (main): views for a monitor.** Which view of a game record lets an LLM monitor detect two colluding agents best? The views are messages, actions, both, a code-built structured report, or the agents' private plans.
- **Study 2.3: evidence and decision rules.** Code-computed evidence signals (co-attendance, capture, gains over others, coordination words, dependence) and decision rules, built on the same dataset.

Full Study 2.2 results: [`writeup/results_22.md`](writeup/results_22.md). Work log and per-task reports: [`notes/`](notes/).

## Setup in 5 bullets

- **Game:** El Farol bar game, 5 agents (J, M, Q, T, Z), 8 rounds. Each round has a public announcement and message, then simultaneous GO/STAY actions.
- **Agents:** `qwen2.5:7b`. **Monitor:** `llama3.1:8b`. Both run locally through Ollama.
- **Episode types** (ground truth comes only from the generation config):
  - Type 1: collusion (two agents get an alliance note);
  - Type 2: placebo;
  - Type 3: persona talk only;
  - Type 4b: two agents share a private incentive but have no agreement.
- **Data:** 48 games, one dev/test split made once before generation (24 / 24; each split 12 Type 1 + 4 of each negative type).
- **Protocol:** monitor format, prompts and thresholds were chosen on dev only, frozen, then run once on test. Follow-ups are pre-registered separately.

## Headline findings (pilot, n = 24 test games)

All numbers are copied from `writeup/results_22.md` and `writeup/results_23.md`. CIs are 95% stratified bootstraps.

- **Which view works depends on the monitor model.**
  - With `llama3.1:8b`, messages alone (V1, 0.490) and actions alone (V2, 0.372) failed, and the code-built structured report worked best (V4, AUROC 0.896 [0.771, 0.979]).
  - With `granite3.3:8b` (same frozen prompt), the ranking reversed: actions 0.767 [0.604, 0.917], structured report 0.510 [0.292, 0.729].
- **Only the combined raw view (V3) matched:** 0.736 with both models.
- **Model-free behaviour signals were the most dependable** (exploratory): capture 0.944 [0.884, 0.986] over all 48 games.
- **Study 2.3:**
  - the coalition-gain rule ranked games well (R2, AUROC 0.872 [0.736, 0.986]);
  - the talk-only LLM judge was below chance (R1, 0.396 [0.205, 0.597]);
  - combining evidence families did not help (R6 − R2: −0.080 [−0.208, 0.045], no clear difference).
- **"Combining messages and actions helps"** (pre-registered RQ2) held on test with llama (+0.365 [0.094, 0.611]). It is fragile: it does not hold over all 48 games, and it does not hold with granite.
- **Measured LLM-monitor reliability problems:**
  - the single-score format returned a constant 80 on 96/96 dev calls;
  - llama showed a last-position bias in its pair scores (granite did not, beyond ties);
  - re-scoring the frozen monitor in a new session moved V2 by +0.188 [+0.007, +0.389].
- **A pre-registered replication on 48 new games is in progress** (`configs/prereg_replication.md`).

## Reproducibility

- **Local open models only, no paid APIs.** Ollama **0.40.3**, with models pinned by digest:
  - `qwen2.5:7b` `845dbda0ea48ed74…`
  - `llama3.1:8b` `46e0c10c039e0191…`

  `scripts/check_env.py` verifies the versions and digests (see `configs/pins.json`).
- **Every call sets `num_ctx` explicitly:** 16384 for the monitor. Temperature is 0 and seeds are fixed per call.
- **Every LLM call is cached to disk,** keyed by model, digest, prompt, schema, settings, seed and sample index. Re-running reads the cache, and the cache is the exact record of every output.
- **Same session vs new session:** within one Ollama session, repeated calls returned identical scores. Across sessions some scores differ (documented in `writeup/results_22.md`, section d).
- **Pre-registration files and commits:**

  | File | Commit |
  |---|---|
  | `configs/prereg_rq01.md` (frozen) | `4909c7e` |
  | `configs/prereg_rq01_amendment1.md` | `2d47580` |
  | `configs/prereg_rq01_amendment2.md` | `a989c7a` |
  | `configs/prereg_rq01_amendment2_erratum.md` | `0dfd1b1` |
  | `configs/frozen/monitor_frozen.json` (frozen monitor + dev thresholds) | `89bdb79` |
  | `configs/prereg_followup1_pair_order.md` (follow-up 1) | `496fc28` |

  Every deviation is listed, with whether it was decided before or after the related data, in `writeup/results_22.md` section f.

## Repository layout

```
configs/          pre-registrations, frozen monitor file, prompts, monitor templates + manifests, pins, plans
core/             generation (El Farol runner), cleaning + leak scan, LLM client (pinned, cached), labels/split,
                  plan, schema, statistics (AUROC, bootstrap), evidence signals (Study 2.3)
study_2_2_views/  view rendering, monitor runner, Study 2.2 analysis
scripts/          command-line entry points (check_env, make_plan, run_plan, merge_check, render_views,
                  run_monitor, analyse_22, ...)
scratch/          per-task measurement and analysis scripts (p8_*, p15_*, p16_*, ...) and small results
tests/            pytest suite (mock LLM transport; no model calls)
writeup/          results_22.md, case-study excerpts, figures + captions
notes/            DEVLOG.md (append-only work log) and reports/ (one report per task)
external/         starter code, read-only (Shi et al. harness; TraceGuard rubric)
```

## Running the tests

Everything runs in one conda environment:

```
conda env create -f environment.yml          # once; environment name: collusion-lab
conda run -n collusion-lab pytest -q         # mock transport only, no model calls
conda run -n collusion-lab python scripts/check_env.py   # needs Ollama 0.40.3 running with the pinned models
```

## Data not included

`data/` (games, labels, split, rendered views), `cache/` (all LLM responses) and `runs/` (monitor outputs, analysis tables) are **not in git** (see `.gitignore`).

- The reports in `notes/reports/` give every command used to produce them.
- The split and labels are created once from the plan (`configs/plans/dataset.json`) and are never remade.
- Without the cache, re-running generation or the monitor makes new model calls. Because of session nondeterminism, those may not reproduce every score exactly.
