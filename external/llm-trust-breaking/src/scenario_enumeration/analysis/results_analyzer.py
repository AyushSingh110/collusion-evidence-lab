"""
Analyze LLM scenario test results and compare with theoretical predictions.

Computes aggregate lying rates, scenario-level statistics, and compares
with theoretical optimal lying behavior.
"""

from typing import Dict, Any, List
import json
from datetime import datetime


def analyze_results(
    results: List[Dict[str, Any]],
    game_type: str
) -> Dict[str, Any]:
    """
    Analyze scenario test results and compute statistics.

    Args:
        results: List of scenario results from run_all_scenarios()
        game_type: Type of game

    Returns:
        Dictionary with analysis results
    """
    total_scenarios = len(results)

    # Detect structure type - single-agent vs multi-agent
    is_single_agent = False
    if results and 'agent_results' not in results[0]:
        # Single-agent mode: data is flat in the scenario
        is_single_agent = True

    if is_single_agent:
        # Single-agent mode: each result is one agent's decision
        total_agents = sum(1 for r in results if r.get('actual_action') is not None)
        total_lying_instances = sum(1 for r in results if r.get('lied', False))

        lying_by_agent = {}
        for result in results:
            if result.get('actual_action') is None:
                continue

            agent_name = result.get('agent_name', 'A')
            if agent_name not in lying_by_agent:
                lying_by_agent[agent_name] = {'lied': 0, 'total': 0}

            lying_by_agent[agent_name]['total'] += 1
            if result.get('lied', False):
                lying_by_agent[agent_name]['lied'] += 1

        scenario_lying_rates = [1.0 if r.get('lied', False) else 0.0
                                for r in results if r.get('actual_action') is not None]
    else:
        # Multi-agent mode: data is nested under agent_results
        total_agents = sum(len(r.get('agent_results', {})) for r in results)

        # Count lying across all scenarios
        total_lying_instances = 0
        lying_by_agent = {}
        scenario_lying_rates = []

        for result in results:
            scenario_lying_rate = result.get('lying_rate', 0)
            scenario_lying_rates.append(scenario_lying_rate)
            total_lying_instances += result.get('lying_count', 0)

            # Track per-agent lying
            for agent_name, agent_data in result.get('agent_results', {}).items():
                if agent_name not in lying_by_agent:
                    lying_by_agent[agent_name] = {'lied': 0, 'total': 0}

                lying_by_agent[agent_name]['total'] += 1
                if agent_data.get('lied', False):
                    lying_by_agent[agent_name]['lied'] += 1

    # Calculate aggregate statistics
    empirical_lying_rate = total_lying_instances / total_agents if total_agents > 0 else 0
    avg_scenario_lying_rate = sum(scenario_lying_rates) / total_scenarios if total_scenarios > 0 else 0

    # Per-agent lying rates
    agent_lying_rates = {}
    for agent_name, stats in lying_by_agent.items():
        agent_lying_rates[agent_name] = stats['lied'] / stats['total'] if stats['total'] > 0 else 0

    # Scenario distribution
    lying_rate_distribution = {}
    for rate in scenario_lying_rates:
        rate_bucket = round(rate, 2)  # Round to 2 decimal places
        lying_rate_distribution[rate_bucket] = lying_rate_distribution.get(rate_bucket, 0) + 1

    # Build analysis result
    analysis = {
        "summary": {
            "game_type": game_type,
            "total_scenarios": total_scenarios,
            "total_agents_tested": total_agents,
            "total_lying_instances": total_lying_instances,
            "empirical_lying_rate": round(empirical_lying_rate, 4),
            "average_scenario_lying_rate": round(avg_scenario_lying_rate, 4)
        },
        "agent_statistics": {
            agent: {
                "lying_rate": round(rate, 4),
                "lied_count": lying_by_agent[agent]['lied'],
                "total_scenarios": lying_by_agent[agent]['total']
            }
            for agent, rate in agent_lying_rates.items()
        },
        "scenario_distribution": {
            "lying_rate_histogram": lying_rate_distribution,
            "min_lying_rate": min(scenario_lying_rates) if scenario_lying_rates else 0,
            "max_lying_rate": max(scenario_lying_rates) if scenario_lying_rates else 0
        }
    }

    return analysis


def save_results(
    results: List[Dict[str, Any]],
    analysis: Dict[str, Any],
    game_type: str,
    n_agents: int,
    output_dir: str = "outputs/experiments",
    model_name: str = None,
    coalition_mode: bool = False,
    assume_honest: bool = False
) -> str:
    """
    Save scenario test results and analysis to file.

    Args:
        results: List of scenario results
        analysis: Analysis dictionary
        game_type: Type of game
        n_agents: Number of agents
        output_dir: Output directory path (now uses game/agents/ structure)
        model_name: Model name for filename (optional, uses old format if not provided)
        coalition_mode: Whether coalition mode was used (adds _coalition suffix)
        assume_honest: Whether assume_honest mode was used (adds _assume_honest suffix)

    Returns:
        Path to saved file
    """
    import os

    # Use new directory structure: game/agents/model_r1.json
    if model_name:
        # New structure
        output_dir = os.path.join(output_dir, game_type, f"{n_agents}agents")
        os.makedirs(output_dir, exist_ok=True)

        # Extract model name without path prefixes
        clean_model_name = model_name.split('/')[-1]

        # Remove :nitro, :free, etc. suffixes from model name for cleaner filenames
        if ':' in clean_model_name:
            clean_model_name = clean_model_name.split(':')[0]

        # Build filename with appropriate suffixes
        suffix = "_r1"
        if coalition_mode:
            suffix += "_coalition"
        if assume_honest:
            suffix += "_assume_honest"
        filename = f"{clean_model_name}{suffix}.json"
        filepath = os.path.join(output_dir, filename)
    else:
        # Old structure for backwards compatibility
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build filename with appropriate suffixes
        suffix = ""
        if coalition_mode:
            suffix += "_coalition"
        if assume_honest:
            suffix += "_assume_honest"
        filename = f"{game_type}_{n_agents}agents_scenarios_{timestamp}{suffix}.json"
        filepath = os.path.join(output_dir, filename)

    # Prepare output data
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "game_type": game_type,
            "n_agents": n_agents,
            "total_scenarios": len(results)
        },
        "analysis": analysis,
        "scenarios": results  # Full scenario-by-scenario results
    }

    # Save to file
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {filepath}")
    return filepath


def print_summary(analysis: Dict[str, Any]):
    """
    Print a human-readable summary of the analysis.

    Args:
        analysis: Analysis dictionary from analyze_results()
    """
    summary = analysis['summary']
    agent_stats = analysis.get('agent_statistics', {})
    theoretical = analysis.get('theoretical_comparison', {})

    print(f"\n{'='*80}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Game Type: {summary['game_type']}")
    print(f"Total Scenarios: {summary['total_scenarios']:,}")
    print(f"Total Agents Tested: {summary['total_agents_tested']:,}")
    print(f"Total Lying Instances: {summary['total_lying_instances']:,}")
    print()
    print(f"EMPIRICAL LYING RATE: {summary['empirical_lying_rate']:.2%}")

    if theoretical:
        print()
        print(f"{'='*80}")
        print(f"THEORETICAL COMPARISON")
        print(f"{'='*80}")
        print(f"Theoretical Optimal Rate: {theoretical['theoretical_lying_rate']:.2%}")
        print(f"Empirical LLM Rate:       {theoretical['empirical_lying_rate']:.2%}")
        print(f"Difference:               {theoretical['difference']:+.2%}")
        print(f"Relative Difference:      {theoretical['relative_difference_pct']:+.1f}%")

    print()
    print(f"{'='*80}")
    print(f"PER-AGENT LYING RATES")
    print(f"{'='*80}")
    for agent, stats in sorted(agent_stats.items()):
        print(f"Agent {agent}: {stats['lying_rate']:.2%} ({stats['lied_count']}/{stats['total_scenarios']})")

    print(f"{'='*80}\n")
