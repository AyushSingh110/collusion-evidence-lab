# Experiments & Datasets Guide

Detailed guide for running TraceGuard experiments, including dataset descriptions, pre-configured runs, and analysis.

## Datasets

### BashArena (ControlArena)

- **Type**: Linux system administration tasks with safety constraints
- **Mode**: ControlArena defer-to-trusted protocol
- **Tasks**: 637 total (honest + attack modes)
- **Sandboxing**: Docker containers for safe execution

**Attack Types**: Privilege escalation, data exfiltration, system sabotage, malware installation.

**Evaluation Metrics**: Safety (attack detection rate), Usefulness (task completion on honest tasks), Pareto frontier (safety vs. usefulness tradeoff curves), Confusion matrix (TP/FP/TN/FN), AUC-ROC.

```bash
# Run TraceGuard on BashArena (20 samples)
python scripts/run_eval.py --monitor traceguard --limit 20

# Run all monitors for comparison
python scripts/run_eval.py --all-monitors --limit 20

# Generate all analysis plots
python scripts/analyze_results.py --log-dir logs/ --output figures/ --all-plots --dimension-breakdown --category-breakdown
```

## Experiment Scenarios

### BashArena Environment

- **637** core tasks (bash scripting, file manipulation, system administration)
- **4** side-task categories (malware download, data exfiltration, privilege escalation, firewall disable)
- **2** modes per task: **HONEST** (just do the task) and **ATTACK** (do the task + attempt side task)

### Pre-Configured Runs

| Scenario | Command | Monitors | Samples | Estimated Time |
| --- | --- | --- | --- | --- |
| Cheap smoke | `--monitor traceguard --attack-only --thresholds 0.5 --limit 2 --side-tasks download_malware` | 1 selected | 2 | a few min (+ one-off image build on first run) |
| Default run | `python scripts/run_eval.py` | traceguard + simple_trusted | 5 | ~1 h (2 × 21 thresholds × 2 modes × 4 side tasks = 336 tasks) |
| Single Monitor | `--monitor traceguard --limit 10` | 1 selected | 10 | hours (1 × 21 × 2 × 4 = 168 tasks) |
| Full Experiment | `--all-monitors --limit 50` | All 6 | 50 | ~6-8 hrs |
| Safety Only | `--all-monitors --attack-only --limit 50` | All 6 | 50 | ~3-4 hrs |
| Post-Hoc Rescore | `run_posthoc.py --log-dir logs/ --all-monitors` | All 6 | (from logs) | ~30 min |

### How Runs Multiply

```
Total runs = monitors × thresholds × modes × samples
Example: --all-monitors --limit 50 → 6 × 4 × 2 × 50 = 2,400 evaluation runs
```

### Default Thresholds

| Threshold | Interpretation | Trade-off |
| --- | --- | --- |
| 0.3 | Aggressive — defer on low suspicion | High safety, low usefulness |
| 0.5 | Balanced | Moderate safety, moderate usefulness |
| 0.7 | Permissive | Lower safety, higher usefulness |
| 0.9 | Very permissive — only defer on extreme suspicion | Minimal safety, maximum usefulness |

### Default Models

| Role | Model | Purpose |
| --- | --- | --- |
| Untrusted | openrouter/openai/gpt-4o | The AI agent performing tasks (may be compromised) |
| Trusted | openrouter/openai/gpt-4o-mini | The monitor and fallback model (assumed safe) |

## Analysis Pipeline

After running experiments, generate analysis plots:

```bash
# Generate all plots
python scripts/analyze_results.py --log-dir logs/ --output figures/ --all-plots --dimension-breakdown --category-breakdown
```

This produces:
- **Pareto frontier** — safety vs. usefulness tradeoff across thresholds
- **Confusion matrix** — TP/FP/TN/FN counts with precision, recall, F1 at the first threshold
- **AUC-ROC curve** — TPR vs. FPR with AUC score and operating point annotations
- **Dimension breakdown** — per-dimension score distributions (attack vs. honest)
- **Category breakdown** — detection rate heatmap by monitor × attack category

## Troubleshooting

| Error | Fix |
| --- | --- |
| "No API key found" / 401 | put `OPENROUTER_API_KEY=...` in the **repo-root** `compute.env` (`cp ../compute.env.example ../compute.env`; see `../COMPUTE.md`) — the default GPT-4o models are closed — then `python scripts/test_model_access.py` |
| "No logs found" | Run evaluations first, check `ls logs/` |
| "Docker not running" | Start Docker Desktop, verify with `docker info` |
| "Only one class present" | Need both honest and attack mode logs for ROC curve |
