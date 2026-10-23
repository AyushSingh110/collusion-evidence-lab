#!/usr/bin/env python3
"""
Resume incomplete experiments by retrying only failed scenarios.

Reads existing experiment JSON, identifies missing scenarios, and re-runs only those.

Usage:
    python experiments/run_scenario_enumeration_resume.py \
        --input outputs/experiments/fishing_single_agent/5agents/gpt-4o-mini_r1.json
"""

import argparse
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.llm.providers.queued_openrouter import QueuedOpenRouterClient
from src.scenario_enumeration.core.scenario_generator import generate_scenarios, count_scenarios
from src.scenario_enumeration.core.scenario_runner import generate_all_prompts, process_queue_results
from src.scenario_enumeration.analysis.results_analyzer import analyze_results, save_results, print_summary
from tqdm import tqdm
import time


def identify_missing_scenarios(filepath: str):
    """
    Identify which scenarios are missing from an incomplete experiment.

    Returns:
        (game_type, n_agents, model, game_params, missing_scenario_ids)
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    metadata = data['metadata']
    scenarios = data['scenarios']

    game_type = metadata['game_type']
    n_agents = metadata['n_agents']
    model = metadata.get('model', 'gpt-4o-mini')

    # Extract game params from metadata
    game_params = {k: v for k, v in metadata.items()
                   if k not in ['game_type', 'n_agents', 'total_scenarios', 'model', 'timestamp']}

    # Get expected total
    expected_total = metadata['total_scenarios']
    actual_total = len(scenarios)

    # Find missing scenario IDs
    present_ids = set(s['scenario_id'] for s in scenarios)
    all_ids = set(range(expected_total))
    missing_ids = sorted(all_ids - present_ids)

    print(f"Experiment: {game_type}, {n_agents} agents, model={model}")
    print(f"Expected: {expected_total}, Present: {actual_total}, Missing: {len(missing_ids)}")

    return game_type, n_agents, model, game_params, missing_ids, data


def main():
    parser = argparse.ArgumentParser(description="Resume incomplete experiment")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to incomplete experiment JSON file")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Request timeout in seconds (default: 300)")
    parser.add_argument("--max-retries", type=int, default=5,
                        help="Max retry attempts (default: 5)")

    args = parser.parse_args()

    # Identify missing scenarios
    game_type, n_agents, model, game_params, missing_ids, original_data = identify_missing_scenarios(args.input)

    if not missing_ids:
        print("✓ All scenarios already complete!")
        return

    print(f"\nRetrying {len(missing_ids)} missing scenarios...")
    print(f"Missing IDs: {missing_ids[:10]}{'...' if len(missing_ids) > 10 else ''}")

    # Generate agent names
    agent_names = [chr(65 + i) for i in range(n_agents)]

    # Generate ALL prompts (we need the mapping)
    from src.llm.client_factory import create_llm_clients
    llm_client = create_llm_clients(
        model=model,
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        temperature=1.0,
    )[0]

    game_params_for_gen = {**game_params, 'include_reasoning': True, 'assume_honest': False}

    all_prompts, total_scenarios = generate_all_prompts(
        game_type=game_type,
        agent_names=agent_names,
        llm_client=llm_client,
        game_params=game_params_for_gen
    )

    # Filter to only missing scenarios
    missing_prompts = [p for p in all_prompts if p['scenario_id'] in missing_ids]

    print(f"Generated {len(missing_prompts)} prompts for missing scenarios")

    # Execute missing prompts
    queued_client = QueuedOpenRouterClient(
        api_key=settings.OPENROUTER_API_KEY,
        max_workers=50,
        timeout=args.timeout,
        max_retries=args.max_retries
    )

    pbar = tqdm(total=len(missing_prompts), desc="Retrying failed scenarios", unit="req")

    def progress_callback(completed, total):
        pbar.update(1)

    start_time = time.time()
    responses = queued_client.execute_all(
        [p['request'] for p in missing_prompts],
        progress_callback=progress_callback
    )
    pbar.close()

    elapsed_time = time.time() - start_time
    print(f"✓ Completed {len(responses)}/{len(missing_prompts)} retry requests in {elapsed_time:.1f}s")

    # Process new results
    new_results = process_queue_results(
        all_prompts=missing_prompts,
        responses=responses,
        game_type=game_type,
        agent_names=agent_names,
        game_params=game_params_for_gen
    )

    print(f"✓ Successfully recovered {len(new_results)} scenarios")

    # Merge with original data
    original_scenarios = original_data['scenarios']
    all_scenarios = original_scenarios + new_results

    # Sort by scenario_id
    all_scenarios.sort(key=lambda x: x['scenario_id'])

    # Re-analyze
    analysis = analyze_results(all_scenarios, game_type)

    print("\n" + "="*80)
    print("UPDATED RESULTS")
    print("="*80)
    print(f"Total scenarios: {len(all_scenarios)}")
    print(f"Lying rate: {analysis['summary']['empirical_lying_rate']:.1%}")

    # Save updated results
    output_path = args.input.replace('.json', '_complete.json')
    save_results(
        results=all_scenarios,
        analysis=analysis,
        game_type=game_type,
        n_agents=n_agents,
        output_dir=os.path.dirname(output_path),
        model_name=model,
        assume_honest=False
    )

    print(f"\n✓ Saved complete results to: {output_path}")

    # Also overwrite original file
    overwrite = input("\nOverwrite original file? (y/n): ")
    if overwrite.lower() == 'y':
        save_results(
            results=all_scenarios,
            analysis=analysis,
            game_type=game_type,
            n_agents=n_agents,
            output_dir=os.path.dirname(args.input),
            model_name=model,
            assume_honest=False
        )
        print(f"✓ Overwrote: {args.input}")


if __name__ == "__main__":
    main()
