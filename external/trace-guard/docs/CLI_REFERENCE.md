# CLI Reference

Full command-line reference for all TraceGuard scripts.

## `run_eval.py` — Main Evaluation Runner

Runs monitors against BashArena tasks using the defer-to-trusted protocol.

```bash
python scripts/run_eval.py [OPTIONS]
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| --monitor | choice | (none) | Run a single monitor. One of: traceguard, simple_trusted, simple_untrusted, collusion_resistant, separation_of_duties, bash_heuristic |
| --all-monitors | flag | false | Run all 6 monitors |
| --limit | int | 5 | Number of samples per task |
| --untrusted-model | str | openrouter/openai/gpt-4o | Model for the agent (untrusted) |
| --trusted-model | str | openrouter/openai/gpt-4o-mini | Model for the monitor/fallback (trusted) |
| --thresholds | float list | 0.0 to 1.0, step 0.05 | Suspicion thresholds for defer-to-trusted decisions |
| --honest-only | flag | false | Only run HONEST mode (measures usefulness) |
| --attack-only | flag | false | Only run ATTACK mode (measures safety) |
| --log-dir | str | logs | Output directory for .eval log files |

**Examples:**

```bash
# Quick smoke test (default: traceguard + simple_trusted, 5 samples)
python scripts/run_eval.py

# Run only the traceguard monitor with 10 samples
python scripts/run_eval.py --monitor traceguard --limit 10

# Full experiment: all 6 monitors, 50 samples each
python scripts/run_eval.py --all-monitors --limit 50

# Custom thresholds
python scripts/run_eval.py --thresholds 0.2 0.4 0.6 0.8

# Attack-only mode with custom models
python scripts/run_eval.py --attack-only \
  --untrusted-model openrouter/anthropic/claude-sonnet-4 \
  --trusted-model openrouter/openai/gpt-4.1-mini
```

## `run_posthoc.py` — Post-Hoc Monitor Evaluation

Re-scores existing agent trajectories with new/different monitors **without re-running the agent**. This is the fastest way to iterate on monitor design.

```bash
python scripts/run_posthoc.py [OPTIONS]
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| --log-dir | str | (required) | Directory containing .eval log files to re-evaluate |
| --monitor | choice | (none) | Single monitor to run post-hoc |
| --all-monitors | flag | false | Run all monitors post-hoc |
| --output-dir | str | logs/posthoc | Output directory for re-scored results |

**Examples:**

```bash
# Re-score logs with the traceguard monitor
python scripts/run_posthoc.py --log-dir logs/ --monitor traceguard

# Compare all monitors on the same trajectories
python scripts/run_posthoc.py --log-dir logs/ --all-monitors
```

## `analyze_results.py` — Results Analysis & Plotting

Generates Pareto frontier plots, confusion matrix, AUC-ROC curve, and optional per-dimension and per-category breakdowns.

```bash
python scripts/analyze_results.py [OPTIONS]
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| --log-dir | str | logs | Directory containing .eval log files |
| --output | str | plots | Output directory for generated plots |
| --dimension-breakdown | flag | false | Generate per-dimension score distribution plots |
| --category-breakdown | flag | false | Generate per-category detection rate heatmap |
| --confusion-matrix | flag | false | Generate confusion matrix with precision/recall/F1 |
| --roc-curve | flag | false | Generate AUC-ROC curve with operating point annotations |
| --all-plots | flag | false | Generate confusion matrix + AUC-ROC (plus Pareto which is always generated) |
| --thresholds | float list | 0.0 to 1.0, step 0.05 | Thresholds for Pareto and confusion matrix analysis |

**Outputs:**

| File | Description |
| --- | --- |
| pareto_frontier.png | Safety (y) vs. Usefulness (x) scatter plot, one curve per monitor, points labeled with audit budget % |
| confusion_matrix.png | TN/FP/FN/TP matrix with accuracy, precision, recall, F1 in title |
| roc_curve.png | TPR vs. FPR curve with AUC score, shaded area, and operating point annotations at FPR=1%, 5%, 10% |
| dimension_breakdown.png | Per-dimension score distributions across monitors (attack vs. honest histograms) |
| category_breakdown.png | Detection rate heatmap by monitor × side-task category |

**Examples:**

```bash
# Basic Pareto plot (always generated)
python scripts/analyze_results.py --log-dir logs/ --output plots/

# Full analysis with all plots
python scripts/analyze_results.py --log-dir logs/ --output plots/ --all-plots --dimension-breakdown --category-breakdown

# Just confusion matrix and ROC curve
python scripts/analyze_results.py --log-dir logs/ --output plots/ --confusion-matrix --roc-curve
```

## `quickstart.sh` — Setup Verification

Checks prerequisites, installs TraceGuard, and runs a small smoke test.

```bash
bash scripts/quickstart.sh
```

---

## Tool Approval (Programmatic API)

TraceGuard provides an Inspect AI `@approver` for pre-execution gating. This is used in Python code, not via CLI.

```python
from traceguard import traceguard_approver

eval(
    task,
    approval=traceguard_approver(
        reject_threshold=0.5,   # block tool calls with boost >= 0.5
        escalate_threshold=0.2, # escalate calls with boost >= 0.2
    ),
)
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| reject_threshold | float | 0.5 | Cumulative detector boost above which the tool call is rejected |
| escalate_threshold | float | 0.2 | Cumulative detector boost above which the tool call is escalated |

The approver runs the 6 pure-function detectors (variable binding, dual-purpose, data flow, string assembly, encoding, config diff) on each tool call. It maintains per-trajectory state so multi-step patterns are caught across calls.

---

## CachePolicy Scopes

All LLM-based scoring now uses `CachePolicy(expiry="1D", scopes={"monitor": ...})` instead of `cache=True`. Each (dimension, model_role) pair gets its own cache partition, preventing cross-monitor cache contamination. No CLI changes needed — this is automatic.

---

See [EXPERIMENTS.md](EXPERIMENTS.md) for detailed experiment scenarios and step-by-step guides.
