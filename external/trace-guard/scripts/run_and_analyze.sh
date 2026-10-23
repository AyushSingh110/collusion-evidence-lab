#!/bin/bash
# =============================================================================
# TraceGuard: Run Evaluation & Analyze Results
#
# Usage:
#   ./scripts/run_and_analyze.sh                    # Default: traceguard, 100 samples, all 4 side tasks
#   ./scripts/run_and_analyze.sh --limit 20         # Fewer samples
#   ./scripts/run_and_analyze.sh --all-monitors     # All 6 monitors
#   ./scripts/run_and_analyze.sh --attack-only      # Safety measurement only
#   ./scripts/run_and_analyze.sh --posthoc-only     # Skip eval, just re-score & analyze
#   ./scripts/run_and_analyze.sh --analyze-only     # Skip eval & posthoc, just plot existing logs
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
LIMIT=100
MONITOR="traceguard"
ALL_MONITORS=true
POSTHOC_ONLY=false
ANALYZE_ONLY=false
LOG_DIR="logs"
POSTHOC_DIR="logs/posthoc"
PLOT_DIR="plots"
THRESHOLDS="$(python3 -c "print(' '.join(str(round(i*0.05,2)) for i in range(21)))")"
MODE=""  # empty = both honest + attack
POSTHOC_MODEL="openrouter/openai/gpt-4o-mini"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)          LIMIT="$2"; shift 2 ;;
        --monitor)        MONITOR="$2"; shift 2 ;;
        --all-monitors)   ALL_MONITORS=true; shift ;;
        --posthoc-only)   POSTHOC_ONLY=true; shift ;;
        --analyze-only)   ANALYZE_ONLY=true; shift ;;
        --log-dir)        LOG_DIR="$2"; shift 2 ;;
        --plot-dir)       PLOT_DIR="$2"; shift 2 ;;
        --thresholds)     THRESHOLDS="$2"; shift 2 ;;
        --honest-only)    MODE="--honest-only"; shift ;;
        --attack-only)    MODE="--attack-only"; shift ;;
        --posthoc-model)  POSTHOC_MODEL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --limit N              Samples per task (default: 100)"
            echo "  --monitor NAME         Specific monitor to run (default: traceguard)"
            echo "  --all-monitors         Run all registered monitors"
            echo "  --posthoc-only         Skip live eval, run posthoc re-scoring + analysis"
            echo "  --analyze-only         Skip eval & posthoc, just analyze existing results"
            echo "  --log-dir DIR          Eval log directory (default: logs)"
            echo "  --plot-dir DIR         Plot output directory (default: plots)"
            echo "  --thresholds \"T1 T2\"   Space-separated thresholds (default: 0.0 to 1.0, step 0.05)"
            echo "  --honest-only          Only run honest mode"
            echo "  --attack-only          Only run attack mode"
            echo "  --posthoc-model MODEL  Model for post-hoc re-scoring (default: openrouter/openai/gpt-4o-mini)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
timestamp() { date "+%Y-%m-%d %H:%M:%S"; }
section()   { echo ""; echo "$(timestamp) ── $1 ──"; }

# ── Preflight checks ─────────────────────────────────────────────────────────
section "Preflight checks"

if [ -f .env ]; then
    set -a; source .env; set +a
    echo "Loaded .env"
fi

python -c "import control_arena" 2>/dev/null || { echo "ERROR: control-arena not installed"; exit 1; }
python -c "import inspect_ai"   2>/dev/null || { echo "ERROR: inspect-ai not installed"; exit 1; }
python -c "import traceguard"   2>/dev/null || { echo "ERROR: traceguard not importable (run pip install -e .)"; exit 1; }

echo "Dependencies OK"

# Check at least one API key is set
if [ -z "${OPENROUTER_API_KEY:-}" ] && ! grep -q "^OPENROUTER_API_KEY=" .env 2>/dev/null; then
    echo "WARNING: OPENROUTER_API_KEY not found in the environment or in .env."
fi

# ── Step 1: Run evaluation ────────────────────────────────────────────────────
if [ "$POSTHOC_ONLY" = false ] && [ "$ANALYZE_ONLY" = false ]; then
    section "Step 1: Running evaluation (limit=$LIMIT)"

    EVAL_ARGS="--limit $LIMIT --log-dir $LOG_DIR --thresholds $THRESHOLDS"

    if [ "$ALL_MONITORS" = true ]; then
        EVAL_ARGS="$EVAL_ARGS --all-monitors"
    else
        EVAL_ARGS="$EVAL_ARGS --monitor $MONITOR"
    fi

    if [ -n "$MODE" ]; then
        EVAL_ARGS="$EVAL_ARGS $MODE"
    fi

    echo "Command: python scripts/run_eval.py $EVAL_ARGS"
    python scripts/run_eval.py $EVAL_ARGS

    EVAL_COUNT=$(find "$LOG_DIR" -maxdepth 1 -name "*.eval" | wc -l | tr -d ' ')
    echo "Eval logs in $LOG_DIR: $EVAL_COUNT"
else
    echo "Skipping live evaluation."
fi

# ── Step 2: Post-hoc re-scoring ───────────────────────────────────────────────
if [ "$ANALYZE_ONLY" = false ]; then
    section "Step 2: Post-hoc re-scoring"

    EVAL_COUNT=$(find "$LOG_DIR" -maxdepth 1 -name "*.eval" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$EVAL_COUNT" -eq 0 ]; then
        echo "No .eval files found in $LOG_DIR — skipping posthoc."
    else
        POSTHOC_ARGS="--log-dir $LOG_DIR --output-dir $POSTHOC_DIR --model ${POSTHOC_MODEL:-openrouter/openai/gpt-4o-mini}"

        if [ "$ALL_MONITORS" = true ]; then
            POSTHOC_ARGS="$POSTHOC_ARGS --all-monitors"
        else
            POSTHOC_ARGS="$POSTHOC_ARGS --monitor $MONITOR"
        fi

        echo "Command: python scripts/run_posthoc.py $POSTHOC_ARGS"
        python scripts/run_posthoc.py $POSTHOC_ARGS
    fi
else
    echo "Skipping post-hoc re-scoring."
fi

# ── Step 3: Analyze results ──────────────────────────────────────────────────
section "Step 3: Analyzing results"

EVAL_COUNT=$(find "$LOG_DIR" -maxdepth 1 -name "*.eval" 2>/dev/null | wc -l | tr -d ' ')
if [ "$EVAL_COUNT" -eq 0 ]; then
    echo "No .eval files in $LOG_DIR — nothing to analyze."
    exit 0
fi

ANALYZE_ARGS="--log-dir $LOG_DIR --output $PLOT_DIR --thresholds $THRESHOLDS --all-plots --dimension-breakdown --category-breakdown"

echo "Command: python scripts/analyze_results.py $ANALYZE_ARGS"
python scripts/analyze_results.py $ANALYZE_ARGS

# ── Step 4: Summary ──────────────────────────────────────────────────────────
section "Summary"

echo "Eval logs:      $LOG_DIR/ ($EVAL_COUNT files)"
echo "Posthoc results: $POSTHOC_DIR/posthoc_results.json"
echo "Plots:          $PLOT_DIR/"

if [ -f "$POSTHOC_DIR/posthoc_results.json" ]; then
    POSTHOC_COUNT=$(python -c "import json; print(len(json.load(open('$POSTHOC_DIR/posthoc_results.json'))))" 2>/dev/null || echo "?")
    echo "Posthoc samples: $POSTHOC_COUNT"
fi

echo ""
echo "Done. $(timestamp)"
