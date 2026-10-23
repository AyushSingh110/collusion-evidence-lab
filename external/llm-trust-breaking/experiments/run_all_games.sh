#!/bin/bash

#==============================================================================
# Batch runner for the scenario-enumeration protocol (run_scenario_enumeration.py).
# For the main 3-stage protocol use experiments/run_endogenous.py directly.
#
# Runs experiments across all games with specified model and agent count.
# Supports both queue mode (continuous pipeline) and batch mode (wave processing).
#==============================================================================

# Configuration variables

# MODELS - List of models to run (will run each sequentially).
# OpenAI family only, via OpenRouter -- anything else is rejected at startup.
MODELS=(
    "openai/gpt-4o-mini"
    "openai/gpt-4o"
    "openai/gpt-5-mini"
)

# Number of agents to test (3, 4, or 5)
NUM_AGENTS=5

# Execution mode
USE_QUEUE=1  # Set to 1 for queue mode (recommended), 0 for batch mode
BATCH_SIZE=10  # Only used if USE_QUEUE=0
MAX_WORKERS=50  # Number of concurrent workers for queue mode

# Sampling settings
NUM_SAMPLES=5  # Number of times to sample each scenario (1=single, 3=majority vote)

# List of games to run
#GAMES=("fishing" "publicgoods" "weakestlink" "volunteer" "diners" "elfarol")
GAMES=("volunteer" "diners" "elfarol")

# Function to check if experiment already exists
experiment_exists() {
    local game=$1

    # Extract clean model name for filename
    local clean_model=$(echo "$MODEL" | sed 's/.*\///' | sed 's/:.*//')

    local output_dir="outputs/experiments/${game}/${NUM_AGENTS}agents"
    local filename="${clean_model}_r1.json"

    if [ -f "${output_dir}/${filename}" ]; then
        return 0  # File exists
    else
        return 1  # File doesn't exist
    fi
}

echo "======================================================================"
echo "SCENARIO-ENUMERATION EXPERIMENT RUNNER"
echo "======================================================================"
echo "Configuration:"
echo "  Models to run: ${#MODELS[@]}"
for model in "${MODELS[@]}"; do
    echo "    - $model"
done
echo "  Number of agents: $NUM_AGENTS"
echo "  Games to run: ${#GAMES[@]}"
echo "  Samples per scenario: $NUM_SAMPLES"
if [ "$USE_QUEUE" -eq 1 ]; then
    echo "  Execution mode: QUEUE (continuous pipeline)"
    echo "  Max workers: $MAX_WORKERS"
else
    echo "  Execution mode: BATCH (wave processing)"
    echo "  Batch size: $BATCH_SIZE"
fi
echo ""
echo "Auto-skip: Will skip experiments that already have output files"
echo "======================================================================"
echo ""

# Loop through each model
for MODEL in "${MODELS[@]}"; do
    echo ""
    echo "######################################################################"
    echo "# RUNNING EXPERIMENTS FOR MODEL: $MODEL"
    echo "######################################################################"
    echo ""

    # Run each game
    for game in "${GAMES[@]}"; do
        if experiment_exists "$game"; then
            echo "⏭️  Skipping $game - already exists"
        else
            echo "----------------------------------------------------------------------"
            echo "Running $game..."
            echo "----------------------------------------------------------------------"

            # Build command based on execution mode
            if [ "$USE_QUEUE" -eq 1 ]; then
                python3 experiments/run_scenario_enumeration.py \
                    --game "$game" \
                    --agents "$NUM_AGENTS" \
                    --model "$MODEL" \
                    --num-samples "$NUM_SAMPLES" \
                    --batch-size "$BATCH_SIZE" \
                    --use-queue \
                    --reasoning
            else
                python3 experiments/run_scenario_enumeration.py \
                    --game "$game" \
                    --agents "$NUM_AGENTS" \
                    --model "$MODEL" \
                    --num-samples "$NUM_SAMPLES" \
                    --batch-size "$BATCH_SIZE" \
                    --reasoning
            fi

            echo ""
            echo "✓ Completed $game"
            echo ""
        fi
    done

    echo ""
    echo "######################################################################"
    echo "# COMPLETED MODEL: $MODEL"
    echo "######################################################################"
    echo ""
done

echo "======================================================================"
echo "ALL EXPERIMENTS COMPLETED!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - Models run: ${#MODELS[@]}"
for model in "${MODELS[@]}"; do
    echo "      $model"
done
echo "  - Games per model: ${#GAMES[@]}"
echo "  - Total experiments: $((${#MODELS[@]} * ${#GAMES[@]}))"
echo ""
echo "Games tested: ${GAMES[*]}"
echo ""
echo "Results saved to: outputs/experiments/{game}/${NUM_AGENTS}agents/"
echo "======================================================================"
