#!/usr/bin/env python3
"""
Comprehensive scaling analysis for binary games across 3-10 agents.

Analyzes lying rates, missed opportunities, strategic/selfish/altruistic/sabotage
categories, and identifies scaling patterns.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # project root

from src.theory.lying_categories import analyze_decision


def load_all_binary_game_results():
    """Load all experimental results for binary games (3-10 agents)."""
    games = ['volunteer', 'diners', 'elfarol']
    agent_counts = list(range(3, 11))  # 3-10 agents

    results = defaultdict(lambda: defaultdict(dict))

    for game in games:
        for n_agents in agent_counts:
            results_dir = Path(f"outputs/experiments/{game}/{n_agents}agents")

            if not results_dir.exists():
                continue

            for result_file in results_dir.glob("*.json"):
                # Parse model name from filename (e.g., "claude-sonnet-4.5_r1.json")
                model_name = result_file.stem.rsplit('_', 1)[0]

                try:
                    with open(result_file) as f:
                        data = json.load(f)
                        results[game][n_agents][model_name] = data
                except Exception as e:
                    print(f"Error loading {result_file}: {e}")
                    continue

    return results


def analyze_single_result(data: dict, game_type: str, n_agents: int) -> Dict:
    """Analyze a single experimental result file."""
    stats = {
        'total_decisions': 0,
        'total_lies': 0,
        'strategic': 0,
        'selfish': 0,
        'altruistic': 0,
        'sabotaging': 0,
        'missed_opportunities': 0,
        'missed_strategic': 0,
        'missed_selfish': 0,
        'consensus_5_of_5': 0,
        'consensus_4_of_5': 0,
        'consensus_3_of_5': 0,
    }

    game_params = data.get('metadata', {}).get('game_params', {})

    for scenario in data.get('scenarios', []):
        # Get the scenario-level announcements for theory calculations
        scenario_announcements = scenario.get('announcements', {})

        for agent_name, result in scenario.get('agent_results', {}).items():
            announced = result.get('announced')
            actual = result.get('actual')
            lied = result.get('lied', False)

            stats['total_decisions'] += 1

            # Consensus stats
            consensus_stats = result.get('consensus_stats', {})
            if consensus_stats.get('consensus_level') == '5/5':
                stats['consensus_5_of_5'] += 1
            elif consensus_stats.get('consensus_level') == '4/5':
                stats['consensus_4_of_5'] += 1
            elif consensus_stats.get('consensus_level') == '3/5':
                stats['consensus_3_of_5'] += 1

            # Analyze decision
            try:
                analysis = analyze_decision(
                    game_type=game_type + "_single_agent",
                    agent_name=agent_name,
                    announced=announced,
                    actual=actual,
                    scenario=scenario_announcements,
                    game_params=game_params,
                    n_agents=n_agents
                )

                if lied:
                    stats['total_lies'] += 1
                    category = analysis.get('lie_category')
                    if category:
                        stats[category] += 1
                else:
                    # Check for missed opportunities
                    if analysis.get('missed_opportunity', False):
                        stats['missed_opportunities'] += 1

                        # Categorize what type of opportunity was missed
                        payoff_gain = analysis.get('best_payoff_gain', 0)
                        state_change = analysis.get('best_state_change', 0)

                        if payoff_gain > 0 and state_change >= 0:
                            stats['missed_strategic'] += 1
                        elif payoff_gain > 0 and state_change < 0:
                            stats['missed_selfish'] += 1

            except Exception as e:
                print(f"Error analyzing decision for {game_type} {n_agents}agents: {e}")
                continue

    return stats


def compute_rates(stats: Dict) -> Dict:
    """Compute percentage rates from counts."""
    total_decisions = stats['total_decisions']
    total_lies = stats['total_lies']
    missed_opps = stats['missed_opportunities']

    if total_decisions == 0:
        return {}

    rates = {
        'lying_rate': (total_lies / total_decisions * 100) if total_decisions > 0 else 0,
        'missed_opp_rate': (missed_opps / total_decisions * 100) if total_decisions > 0 else 0,
        'exploitation_rate': (total_lies / (total_lies + missed_opps) * 100) if (total_lies + missed_opps) > 0 else 0,
    }

    # Category rates (out of all lies)
    if total_lies > 0:
        rates['strategic_rate'] = stats['strategic'] / total_lies * 100
        rates['selfish_rate'] = stats['selfish'] / total_lies * 100
        rates['altruistic_rate'] = stats['altruistic'] / total_lies * 100
        rates['sabotaging_rate'] = stats['sabotaging'] / total_lies * 100
    else:
        rates['strategic_rate'] = 0
        rates['selfish_rate'] = 0
        rates['altruistic_rate'] = 0
        rates['sabotaging_rate'] = 0

    # Consensus rates
    rates['consensus_5_rate'] = (stats['consensus_5_of_5'] / total_decisions * 100) if total_decisions > 0 else 0
    rates['consensus_4_rate'] = (stats['consensus_4_of_5'] / total_decisions * 100) if total_decisions > 0 else 0
    rates['consensus_3_rate'] = (stats['consensus_3_of_5'] / total_decisions * 100) if total_decisions > 0 else 0

    return rates


def analyze_scaling_patterns():
    """Main analysis function."""
    print("Loading experimental results...")
    results = load_all_binary_game_results()

    # Organize data by game -> model -> agent_count -> stats
    all_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    print("\nAnalyzing results...")
    for game in results:
        for n_agents in results[game]:
            for model in results[game][n_agents]:
                data = results[game][n_agents][model]
                stats = analyze_single_result(data, game, n_agents)
                rates = compute_rates(stats)

                all_stats[game][model][n_agents] = {
                    'counts': stats,
                    'rates': rates
                }

                print(f"Processed: {game}, {model}, {n_agents} agents")

    return all_stats


def generate_report(all_stats: Dict, output_file: str):
    """Generate comprehensive scaling analysis report."""

    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE SCALING ANALYSIS: BINARY GAMES (3-10 AGENTS)\n")
        f.write("="*80 + "\n\n")

        # Get list of all models and games
        all_models = set()
        all_games = list(all_stats.keys())
        for game in all_stats:
            all_models.update(all_stats[game].keys())
        all_models = sorted(all_models)

        # Section 1: Lying Rates by Game and Agent Count
        f.write("\n" + "="*80 + "\n")
        f.write("1. LYING RATES ACROSS AGENT COUNTS\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        lr = all_stats[game][model][n_agents]['rates'].get('lying_rate', 0)
                        row += f" {lr:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 2: Exploitation Rates
        f.write("\n\n" + "="*80 + "\n")
        f.write("2. EXPLOITATION RATES (Lies / (Lies + Missed Opportunities))\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        er = all_stats[game][model][n_agents]['rates'].get('exploitation_rate', 0)
                        row += f" {er:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 3: Strategic Lying Rates (out of all lies)
        f.write("\n\n" + "="*80 + "\n")
        f.write("3. STRATEGIC LYING RATE (% of lies that are strategic)\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        sr = all_stats[game][model][n_agents]['rates'].get('strategic_rate', 0)
                        row += f" {sr:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 4: Selfish Lying Rates
        f.write("\n\n" + "="*80 + "\n")
        f.write("4. SELFISH LYING RATE (% of lies that are selfish)\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        sr = all_stats[game][model][n_agents]['rates'].get('selfish_rate', 0)
                        row += f" {sr:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 5: Altruistic Lying Rates
        f.write("\n\n" + "="*80 + "\n")
        f.write("5. ALTRUISTIC LYING RATE (% of lies that are altruistic)\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        ar = all_stats[game][model][n_agents]['rates'].get('altruistic_rate', 0)
                        row += f" {ar:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 6: Consensus Rates
        f.write("\n\n" + "="*80 + "\n")
        f.write("6. CONSENSUS RATES (5/5 agreement across samples)\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Model':<30} {'3ag':>7} {'4ag':>7} {'5ag':>7} {'6ag':>7} {'7ag':>7} {'8ag':>7} {'9ag':>7} {'10ag':>7}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                row = f"{model:<30}"
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        cr = all_stats[game][model][n_agents]['rates'].get('consensus_5_rate', 0)
                        row += f" {cr:6.1f}%"
                    else:
                        row += f" {'--':>7}"
                f.write(row + "\n")

        # Section 7: Raw Counts
        f.write("\n\n" + "="*80 + "\n")
        f.write("7. RAW COUNTS\n")
        f.write("="*80 + "\n\n")

        for game in all_games:
            for model in all_models:
                if model not in all_stats[game]:
                    continue

                f.write(f"\n{game.upper()} - {model}\n")
                f.write("-"*80 + "\n")
                f.write(f"{'Agents':<10} {'Decisions':>10} {'Lies':>10} {'Strategic':>10} {'Selfish':>10} {'Altruistic':>10} {'Sabotage':>10} {'Missed':>10}\n")
                f.write("-"*80 + "\n")

                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        counts = all_stats[game][model][n_agents]['counts']
                        f.write(f"{n_agents:<10} {counts['total_decisions']:>10} {counts['total_lies']:>10} "
                               f"{counts['strategic']:>10} {counts['selfish']:>10} {counts['altruistic']:>10} "
                               f"{counts['sabotaging']:>10} {counts['missed_opportunities']:>10}\n")

        # Section 8: Scaling Pattern Analysis
        f.write("\n\n" + "="*80 + "\n")
        f.write("8. SCALING PATTERN ANALYSIS\n")
        f.write("="*80 + "\n\n")

        f.write("Analyzing trends as group size increases from 3 to 10 agents:\n\n")

        for game in all_games:
            f.write(f"\n{game.upper()}\n")
            f.write("-"*80 + "\n")

            for model in all_models:
                if model not in all_stats[game]:
                    continue

                # Get lying rates for available agent counts
                lying_rates = []
                agent_counts = []
                for n_agents in range(3, 11):
                    if n_agents in all_stats[game][model]:
                        lr = all_stats[game][model][n_agents]['rates'].get('lying_rate', 0)
                        lying_rates.append(lr)
                        agent_counts.append(n_agents)

                if len(lying_rates) < 2:
                    continue

                # Simple trend analysis
                avg_3_5 = sum([lr for n, lr in zip(agent_counts, lying_rates) if n <= 5]) / len([n for n in agent_counts if n <= 5]) if any(n <= 5 for n in agent_counts) else 0
                avg_6_10 = sum([lr for n, lr in zip(agent_counts, lying_rates) if n >= 6]) / len([n for n in agent_counts if n >= 6]) if any(n >= 6 for n in agent_counts) else 0

                change = avg_6_10 - avg_3_5

                trend = "increasing" if change > 2 else ("decreasing" if change < -2 else "stable")

                f.write(f"{model}:\n")
                f.write(f"  Lying rate 3-5 agents: {avg_3_5:.1f}%\n")
                f.write(f"  Lying rate 6-10 agents: {avg_6_10:.1f}%\n")
                f.write(f"  Change: {change:+.1f}pp ({trend})\n")
                f.write(f"  Range: {min(lying_rates):.1f}% - {max(lying_rates):.1f}%\n\n")

        f.write("\n" + "="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")


def main():
    print("Starting comprehensive scaling analysis...")

    all_stats = analyze_scaling_patterns()

    output_file = "outputs/SCALING_ANALYSIS.txt"
    generate_report(all_stats, output_file)

    print(f"\n✓ Analysis complete! Report saved to {output_file}")

    # Print summary
    print("\nSummary:")
    for game in all_stats:
        for model in all_stats[game]:
            agent_counts = sorted(all_stats[game][model].keys())
            print(f"  {game} - {model}: {len(agent_counts)} agent counts ({min(agent_counts)}-{max(agent_counts)})")


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
