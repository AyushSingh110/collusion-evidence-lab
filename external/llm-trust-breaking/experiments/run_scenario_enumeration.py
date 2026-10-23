"""
Main script to run scenario enumeration experiments.

This script tests LLM behavior across all possible announcement scenarios
and compares empirical lying rates to theoretical predictions.

Usage:
    python run_scenario_experiment.py --game attack --agents 5 --model gpt-4o-mini
"""

import argparse
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.llm.client_factory import create_llm_clients
from src.scenario_enumeration.core.scenario_runner import run_all_scenarios, generate_all_prompts, process_queue_results
from src.scenario_enumeration.analysis.results_analyzer import analyze_results, save_results, print_summary
from src.llm.providers.queued_openrouter import QueuedOpenRouterClient
from tqdm import tqdm
import time


def main():
    parser = argparse.ArgumentParser(description="Run scenario enumeration experiment")
    parser.add_argument("--game", type=str, default="fishing",
                        choices=["fishing", "publicgoods", "weakestlink", "elfarol", "volunteer", "diners"],
                        help="Game type to test")
    parser.add_argument("--agents", type=int, default=5,
                        help="Number of agents")
    parser.add_argument("--model", type=str, default=None,
                        help="LLM model to use. If not specified, uses MODEL from .env for OpenAI or OPENROUTER_MODEL for OpenRouter")
    parser.add_argument("--temperature", type=float, default=1.0,
                        help="Sampling temperature (0.0-2.0, default: 1.0)")
    parser.add_argument("--num-samples", type=int, default=1,
                        help="Number of times to sample each scenario. Use 1 (default) for single response, or higher (e.g., 3) to test response variance. Multiple samples are aggregated by majority vote.")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Batch size for parallel execution")
    parser.add_argument("--output-dir", type=str, default="outputs/experiments",
                        help="Output directory for results")
    parser.add_argument("--reasoning", action="store_true",
                        help="Include reasoning field in LLM responses. Increases output tokens but provides explanation for decisions.")
    parser.add_argument("--num-rounds", type=int, default=1,
                        help="Number of rounds to play (default: 1 for single-round). Use >1 for multi-turn games.")
    parser.add_argument("--load-round1", type=str, default=None,
                        help="Path to existing single-round experiment JSON to use as Round 1 for multi-turn games")
    parser.add_argument("--use-queue", action="store_true",
                        help="Use queue-based continuous pipeline instead of wave batching for better efficiency")
    parser.add_argument("--assume-honest", action="store_true",
                        help="Add assumption that other agents stick to their announcements in decision-making prompt")

    # Game-specific parameters
    parser.add_argument("--total-fish", type=int, default=100,
                        help="[Fishing] Total fish in lake")
    parser.add_argument("--threshold", type=int, default=50,
                        help="[Fishing] Collapse threshold")
    parser.add_argument("--max-catch", type=int, default=5,
                        help="[Fishing] Max catch per agent (default: 5)")
    parser.add_argument("--initial-tokens", type=int, default=5,
                        help="[Public Goods] Initial tokens per agent (default: 5)")
    parser.add_argument("--multiplier", type=float, default=1.5,
                        help="[Public Goods] Public pool multiplier")
    parser.add_argument("--elfarol-threshold", type=float, default=0.5,
                        help="[El Farol] Bar capacity threshold (0.0-1.0, default: 0.5 = at least half)")
    parser.add_argument("--expensive-joy", type=float, default=10.0,
                        help="[Diners] Joy from expensive dish (default: 10.0)")
    parser.add_argument("--cheap-joy", type=float, default=5.0,
                        help="[Diners] Joy from cheap dish (default: 5.0)")
    parser.add_argument("--expensive-cost", type=float, default=8.0,
                        help="[Diners] Cost of expensive dish (default: 8.0)")
    parser.add_argument("--cheap-cost", type=float, default=2.0,
                        help="[Diners] Cost of cheap dish (default: 2.0)")
    parser.add_argument("--max-effort", type=int, default=5,
                        help="[Weakest Link] Maximum effort level (default: 5, so 0-5 range)")
    parser.add_argument("--cost-per-effort", type=float, default=2.0,
                        help="[Weakest Link] Cost per unit of effort (default: 2.0)")
    parser.add_argument("--benefit-per-min-effort", type=float, default=3.0,
                        help="[Weakest Link] Benefit per unit of minimum effort (default: 3.0)")

    args = parser.parse_args()

    # Determine which model to use based on provider
    if args.model is None:
        model = settings.MODEL   # the resolved default model (from the repo-root compute.env, else the fallback)
    else:
        model = args.model

    # Generate agent names - use random letters to avoid alphabetic/position bias
    import random
    import string
    random.seed(42)  # Fixed seed for reproducibility
    alphabet = list(string.ascii_uppercase)
    random.shuffle(alphabet)
    agent_names = alphabet[:args.agents]  # e.g., ['M', 'Q', 'F', 'X', 'K'] instead of ['A', 'B', 'C', 'D', 'E']
    agent_names.sort()  # Sort for consistency in output, but they're still non-sequential
    print(f"Using randomized agent names: {agent_names}")

    # Initialize LLM clients (inference via the shared repo-root compute.env config)
    llm_client, parallel_client = create_llm_clients(
        model=model,
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        temperature=args.temperature,
        max_workers=20
    )

    # Build game parameters
    game_params = {}
    if args.game == "fishing_single_agent":
        # Use adaptive threshold: 3 * number of agents (unless explicitly overridden)
        adaptive_threshold = 3 * args.agents
        threshold = adaptive_threshold if args.threshold == 50 else args.threshold
        game_params = {
            'total_fish': args.total_fish,
            'collapse_threshold': threshold,
            'max_catch_per_agent': args.max_catch,
            'max_catch': args.max_catch  # For scenario generation
        }
    elif args.game == "publicgoods_single_agent":
        game_params = {
            'initial_tokens': args.initial_tokens,
            'multiplier': args.multiplier
        }
    elif args.game == "elfarol_single_agent":
        game_params = {
            'elfarol_threshold': args.elfarol_threshold,
            'threshold': args.elfarol_threshold
        }
    elif args.game == "volunteer_single_agent":
        game_params = {}
    elif args.game == "diners_single_agent":
        game_params = {
            'expensive_joy': args.expensive_joy,
            'cheap_joy': args.cheap_joy,
            'expensive_cost': args.expensive_cost,
            'cheap_cost': args.cheap_cost
        }
    elif args.game == "weakestlink_single_agent":
        game_params = {
            'max_effort': args.max_effort,
            'cost_per_effort': args.cost_per_effort,
            'benefit_per_min_effort': args.benefit_per_min_effort
        }

    # Add include_reasoning flag to game_params
    game_params['include_reasoning'] = args.reasoning
    game_params['assume_honest'] = args.assume_honest

    # Handle num_samples: how many times to sample each scenario
    num_samples = args.num_samples
    if num_samples > 1:
        print(f"\n🔁 Sampling each scenario {num_samples} times (majority vote aggregation)")
    else:
        print(f"\n📋 Sampling each scenario once (single response per scenario)")

    game_params['num_samples'] = num_samples

    if not args.reasoning:
        print("\n⚡ Running in action-only mode (action-only mode) - 55% cost savings!")

    # Run experiment
    if args.use_queue and args.num_rounds == 1:
        # Queue-based execution (only for single-round experiments)
        print("\n" + "="*80)
        print("USING QUEUE-BASED CONTINUOUS PIPELINE")
        print("="*80)
        print("✓ Pre-generating all prompts upfront")
        print("✓ Workers pull continuously from queue")
        print("✓ No wave batching - maximum efficiency")
        print("="*80 + "\n")

        # Step 1: Generate all prompts upfront
        print("Step 1: Generating all prompts...")
        all_prompts, total_scenarios = generate_all_prompts(
            game_type=args.game,
            agent_names=agent_names,
            llm_client=llm_client,
            game_params=game_params
        )
        print(f"✓ Generated {len(all_prompts)} prompts for {total_scenarios} scenarios\n")

        # Step 2: Execute via queue with progress bar
        print("Step 2: Executing requests via continuous pipeline...")

        # Create queued client
        queued_client = QueuedOpenRouterClient(
            api_key=settings.OPENROUTER_API_KEY,
            max_workers=50,
            timeout=60,  # 1 minute timeout per request
            max_retries=5  # 5 retry attempts to handle transient failures
        )

        # Progress bar callback
        pbar = tqdm(total=len(all_prompts), desc="API requests", unit="req")

        def progress_callback(completed, total):
            pbar.update(1)

        start_time = time.time()

        # Execute all requests
        responses = queued_client.execute_all(
            [p['request'] for p in all_prompts],
            progress_callback=progress_callback
        )

        pbar.close()
        elapsed_time = time.time() - start_time

        print(f"✓ Completed {len(responses)}/{len(all_prompts)} requests in {elapsed_time:.1f}s")
        print(f"  Average: {elapsed_time/len(all_prompts):.2f}s per request\n")

        # Step 3: Process results
        print("Step 3: Processing results and aggregating...")
        results = process_queue_results(
            all_prompts=all_prompts,
            responses=responses,
            game_type=args.game,
            agent_names=agent_names
        )
        print(f"✓ Processed {len(results)} scenarios\n")

        print("="*80)
        print("QUEUE EXECUTION COMPLETE")
        print("="*80)
        print(f"Total scenarios: {total_scenarios:,}")
        print(f"Total requests: {len(all_prompts):,}")
        print(f"Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
        print(f"Average per scenario: {elapsed_time/total_scenarios:.2f}s")
        print("="*80 + "\n")

    elif args.use_queue and args.num_rounds > 1:
        print("\n⚠️  Warning: --use-queue is only supported for single-round experiments (--num-rounds 1)")
        print("    Falling back to standard batch execution...\n")
        results = run_all_scenarios(
            game_type=args.game,
            agent_names=agent_names,
            llm_client=llm_client,
            parallel_client=parallel_client,
            game_params=game_params,
            batch_size=args.batch_size,
            progress=True,
            num_rounds=args.num_rounds,
            load_round1_path=args.load_round1
        )
    else:
        # Standard batch execution
        results = run_all_scenarios(
            game_type=args.game,
            agent_names=agent_names,
            llm_client=llm_client,
            parallel_client=parallel_client,
            game_params=game_params,
            batch_size=args.batch_size,
            progress=True,
            num_rounds=args.num_rounds,
            load_round1_path=args.load_round1
        )

    # Analyze results
    analysis = analyze_results(
        results=results,
        game_type=args.game
    )

    # Print summary
    print_summary(analysis)

    # Save results
    save_results(
        results=results,
        analysis=analysis,
        game_type=args.game,
        n_agents=args.agents,
        output_dir=args.output_dir,
        model_name=model,
        assume_honest=args.assume_honest
    )


if __name__ == "__main__":
    main()
