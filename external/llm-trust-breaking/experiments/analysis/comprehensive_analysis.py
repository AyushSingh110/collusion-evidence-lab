"""
Comprehensive analysis of all experimental results.

Analyzes all result files and generates tables showing:
- Overall lying rates
- Strategic/selfish lying rates
- Altruistic lying rates
- Sabotage rates
- Missed opportunity rates

Organized by game, model, and agent count.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root

from src.theory.lying_categories import analyze_decision


def normalize_game_type(game_type: str) -> str:
    """Normalize game type to match theory code expectations."""
    if game_type.endswith("_single_agent"):
        return game_type
    return f"{game_type}_single_agent"


def load_result_file(filepath: str) -> Dict[str, Any]:
    """Load a single result file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_game_params(game_type: str, n_agents: int) -> Dict[str, Any]:
    """Get default game parameters for a game type."""
    if game_type in ["fishing", "fishing_single_agent"]:
        return {'max_catch_per_agent': 5, 'collapse_threshold': n_agents * 3}
    elif game_type in ["publicgoods", "publicgoods_single_agent"]:
        return {'initial_tokens': 5, 'multiplier': 1.5}
    elif game_type in ["weakestlink", "weakestlink_single_agent"]:
        return {'max_effort': 5, 'cost_per_effort': 2.0, 'benefit_per_min_effort': 3.0}
    elif game_type in ["diners", "diners_single_agent"]:
        return {'expensive_joy': 10.0, 'cheap_joy': 5.0, 'expensive_cost': 8.0, 'cheap_cost': 2.0}
    elif game_type in ["elfarol", "elfarol_single_agent"]:
        return {'threshold': 0.5, 'bar_uncrowded_payout': 10.0, 'bar_crowded_payout': -5.0, 'home_payout': 0.0}
    elif game_type in ["volunteer", "volunteer_single_agent"]:
        return {'cooperate_payout': 0.0, 'defect_success_payout': 1.0, 'defect_fail_payout': -5.0}
    else:
        return {}


def analyze_result_file(result_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single result file and return summary statistics.

    Returns:
        Dict with counts for:
        - total_decisions
        - total_lies
        - strategic_lies (payoff increases, state stays same or improves)
        - selfish_lies (payoff increases, state worsens)
        - altruistic_lies (payoff decreases, state improves)
        - sabotage_lies (all other harmful lies)
        - missed_opportunities (didn't lie when it would be strategic)
    """
    game_type = normalize_game_type(result_data['metadata']['game_type'])
    n_agents = result_data['metadata']['n_agents']
    game_params = extract_game_params(game_type, n_agents)

    stats = {
        'total_decisions': 0,
        'total_lies': 0,
        'strategic_lies': 0,
        'selfish_lies': 0,
        'altruistic_lies': 0,
        'sabotage_lies': 0,
        'missed_opportunities': 0,
    }

    for scenario in result_data['scenarios']:
        announcements = scenario['announcements']

        # Get agent name from announcements (single agent experiments use 'agent_name' field)
        agent_name = announcements.get('agent_name')
        if not agent_name:
            # Fallback: get first agent from agent_results
            agent_name = list(scenario['agent_results'].keys())[0]

        for agent, result in scenario['agent_results'].items():
            announced = result['announced']
            actual = result['actual']

            stats['total_decisions'] += 1

            # Analyze this decision
            analysis = analyze_decision(
                game_type=game_type,
                agent_name=agent_name,  # Use agent_name from announcements
                announced=announced,
                actual=actual,
                scenario=announcements,
                game_params=game_params,
                n_agents=n_agents
            )

            if analysis['lied']:
                stats['total_lies'] += 1
                category = analysis['lie_category']

                if category == 'strategic':
                    stats['strategic_lies'] += 1
                elif category == 'selfish':
                    stats['selfish_lies'] += 1
                elif category == 'altruistic':
                    stats['altruistic_lies'] += 1
                elif category == 'sabotaging':
                    stats['sabotage_lies'] += 1
            else:
                if analysis['missed_opportunity']:
                    stats['missed_opportunities'] += 1

    return stats


def collect_all_results() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Collect all experimental results.

    Returns:
        Nested dict: {game: {n_agents: {model: stats}}}
    """
    results = defaultdict(lambda: defaultdict(dict))

    experiments_dir = Path(__file__).parent.parent / "outputs" / "experiments"

    games = ['fishing', 'publicgoods', 'weakestlink', 'volunteer', 'diners', 'elfarol']
    agent_counts = [3, 4, 5]

    for game in games:
        for n_agents in agent_counts:
            agent_dir = experiments_dir / game / f"{n_agents}agents"

            if not agent_dir.exists():
                continue

            for result_file in agent_dir.glob("*_r1.json"):
                model_name = result_file.stem.replace("_r1", "")

                print(f"Analyzing {game}/{n_agents}agents/{model_name}...")

                try:
                    result_data = load_result_file(result_file)
                    stats = analyze_result_file(result_data)
                    results[game][n_agents][model_name] = stats
                except Exception as e:
                    print(f"  ERROR: {e}")
                    continue

    return results


def compute_rates(stats: Dict[str, int]) -> Dict[str, float]:
    """Compute percentage rates from raw counts."""
    total = stats['total_decisions']
    if total == 0:
        return {
            'lying_rate': 0.0,
            'strategic_rate': 0.0,
            'selfish_rate': 0.0,
            'altruistic_rate': 0.0,
            'sabotage_rate': 0.0,
            'missed_opp_rate': 0.0,
        }

    total_lies = stats['total_lies']

    return {
        'lying_rate': 100 * stats['total_lies'] / total,
        'strategic_rate': 100 * stats['strategic_lies'] / total,
        'selfish_rate': 100 * stats['selfish_lies'] / total,
        'altruistic_rate': 100 * stats['altruistic_lies'] / total,
        'sabotage_rate': 100 * stats['sabotage_lies'] / total,
        'missed_opp_rate': 100 * stats['missed_opportunities'] / total,
    }


def generate_tables(results: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
    """Generate formatted tables from results."""

    output = []
    output.append("=" * 100)
    output.append("COMPREHENSIVE ANALYSIS - ALL EXPERIMENTS")
    output.append("=" * 100)
    output.append("")

    # Get all unique models
    all_models = set()
    for game_data in results.values():
        for agent_data in game_data.values():
            all_models.update(agent_data.keys())

    models = sorted(all_models)
    games = sorted(results.keys())
    agent_counts = [3, 4, 5]

    # Table 1: Overall Lying Rates
    output.append("\n" + "=" * 100)
    output.append("TABLE 1: OVERALL LYING RATES (%)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        # Header
        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        # Each model
        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['lying_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            # Average
            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    # Table 2: Strategic Lying Rates
    output.append("\n\n" + "=" * 100)
    output.append("TABLE 2: STRATEGIC LYING RATES (% - lying when payoff increases & state doesn't worsen)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['strategic_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    # Table 3: Selfish Lying Rates
    output.append("\n\n" + "=" * 100)
    output.append("TABLE 3: SELFISH LYING RATES (% - lying when payoff increases but state worsens)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['selfish_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    # Table 4: Missed Opportunities
    output.append("\n\n" + "=" * 100)
    output.append("TABLE 4: MISSED OPPORTUNITIES (% - didn't lie when strategic lying was available)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['missed_opp_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    # Table 5: Altruistic Lying
    output.append("\n\n" + "=" * 100)
    output.append("TABLE 5: ALTRUISTIC LYING RATES (% - lying hurts self but helps collective)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['altruistic_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    # Table 6: Sabotage Lying
    output.append("\n\n" + "=" * 100)
    output.append("TABLE 6: SABOTAGE RATES (% - lying that harms without strategic benefit)")
    output.append("=" * 100)

    for n_agents in agent_counts:
        output.append(f"\n{n_agents} AGENTS:")
        output.append("-" * 100)

        header = f"{'Model':<25}"
        for game in games:
            header += f"{game:<15}"
        header += f"{'Average':<15}"
        output.append(header)
        output.append("-" * 100)

        for model in models:
            row = f"{model:<25}"
            rates = []

            for game in games:
                if game in results and n_agents in results[game] and model in results[game][n_agents]:
                    stats = results[game][n_agents][model]
                    rate_dict = compute_rates(stats)
                    rate = rate_dict['sabotage_rate']
                    rates.append(rate)
                    row += f"{rate:>6.1f}%{' ':<8}"
                else:
                    row += f"{'---':<15}"

            if rates:
                avg = sum(rates) / len(rates)
                row += f"{avg:>6.1f}%"
            else:
                row += f"{'---':<15}"

            output.append(row)

    output.append("\n" + "=" * 100)
    output.append("END OF ANALYSIS")
    output.append("=" * 100)

    return "\n".join(output)


def main():
    print("Starting comprehensive analysis...")
    print()

    # Collect all results
    results = collect_all_results()

    print()
    print("Generating tables...")

    # Generate tables
    tables = generate_tables(results)

    # Print to console
    print()
    print(tables)

    # Save to file
    output_file = Path(__file__).parent.parent / "outputs" / "COMPREHENSIVE_ANALYSIS.txt"
    with open(output_file, 'w') as f:
        f.write(tables)

    print()
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, KeyError) as e:
        sys.exit(
            "\nThis script analyses result files from the original study, and the ones it\n"
            f"expects were not found under outputs/ ({e!r}).\n"
            "Run the matching experiment first, or point the paths at the top of this\n"
            "file at your own results."
        )
