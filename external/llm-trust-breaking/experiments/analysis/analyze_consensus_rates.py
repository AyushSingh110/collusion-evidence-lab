#!/usr/bin/env python3
"""
Analyze consensus rates from majority voting across samples.

For each scenario, we run 5 independent samples and use majority voting.
This script analyzes how often the 5 samples agree.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, Any, List

def load_result_file(filepath: str) -> Dict[str, Any]:
    """Load a single result file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_consensus_stats():
    """Analyze consensus statistics across all experiments."""

    # Storage for consensus data
    consensus_data = defaultdict(lambda: {
        'distribution': Counter(),  # Count of each consensus level
        'rates': [],  # All consensus rates for averaging
        'unanimous_count': 0,
        'total_scenarios': 0
    })

    # Also store by model and by game
    by_model = defaultdict(lambda: {
        'distribution': Counter(),
        'rates': [],
        'unanimous_count': 0,
        'total_scenarios': 0
    })

    by_game = defaultdict(lambda: {
        'distribution': Counter(),
        'rates': [],
        'unanimous_count': 0,
        'total_scenarios': 0
    })

    experiments_dir = Path(__file__).parent.parent / "outputs" / "experiments"

    games = ['fishing', 'publicgoods', 'weakestlink', 'volunteer', 'diners', 'elfarol']
    agent_counts = [3, 4, 5]

    print("Analyzing consensus rates from majority voting...")
    print()

    for game in games:
        for n_agents in agent_counts:
            agent_dir = experiments_dir / game / f"{n_agents}agents"

            if not agent_dir.exists():
                continue

            for result_file in agent_dir.glob("*_r1.json"):
                model_name = result_file.stem.replace("_r1", "")

                try:
                    result_data = load_result_file(result_file)

                    for scenario in result_data.get('scenarios', []):
                        for agent, agent_result in scenario.get('agent_results', {}).items():
                            consensus_stats = agent_result.get('consensus_stats', {})

                            if not consensus_stats:
                                continue

                            consensus_rate = consensus_stats.get('consensus_rate', 0.0)
                            is_unanimous = consensus_stats.get('is_unanimous', False)
                            num_responses = consensus_stats.get('num_responses', 5)

                            # Determine agreement level (5/5, 4/5, 3/5, etc.)
                            num_agree = int(consensus_rate * num_responses)
                            agreement_key = f"{num_agree}/{num_responses}"

                            # Store in overall stats
                            key = f"{game}_{n_agents}agents_{model_name}"
                            consensus_data[key]['distribution'][agreement_key] += 1
                            consensus_data[key]['rates'].append(consensus_rate)
                            consensus_data[key]['total_scenarios'] += 1
                            if is_unanimous:
                                consensus_data[key]['unanimous_count'] += 1

                            # Store by model
                            by_model[model_name]['distribution'][agreement_key] += 1
                            by_model[model_name]['rates'].append(consensus_rate)
                            by_model[model_name]['total_scenarios'] += 1
                            if is_unanimous:
                                by_model[model_name]['unanimous_count'] += 1

                            # Store by game
                            game_key = f"{game}_{n_agents}agents"
                            by_game[game_key]['distribution'][agreement_key] += 1
                            by_game[game_key]['rates'].append(consensus_rate)
                            by_game[game_key]['total_scenarios'] += 1
                            if is_unanimous:
                                by_game[game_key]['unanimous_count'] += 1

                except Exception as e:
                    print(f"Error processing {result_file}: {e}")
                    continue

    return consensus_data, by_model, by_game


def format_distribution(distribution: Counter, total: int) -> str:
    """Format distribution as percentages."""
    lines = []
    # Sort by agreement level (5/5, 4/5, 3/5, etc.)
    for key in sorted(distribution.keys(), reverse=True):
        count = distribution[key]
        pct = 100 * count / total if total > 0 else 0
        lines.append(f"    {key}: {count:5d} ({pct:5.1f}%)")
    return "\n".join(lines)


def generate_report(consensus_data, by_model, by_game):
    """Generate formatted report."""

    output = []
    output.append("=" * 100)
    output.append("CONSENSUS RATE ANALYSIS - MAJORITY VOTING AGREEMENT")
    output.append("=" * 100)
    output.append("")
    output.append("For each scenario, we query the model 5 times independently and use majority voting.")
    output.append("This analysis shows how often the 5 samples agree with each other.")
    output.append("")
    output.append("Consensus levels:")
    output.append("  5/5 = All 5 samples agree (unanimous)")
    output.append("  4/5 = 4 out of 5 samples agree (80% consensus)")
    output.append("  3/5 = 3 out of 5 samples agree (60% consensus, simple majority)")
    output.append("  2/5 or less = No clear majority")
    output.append("")

    # ========================================
    # BY MODEL SUMMARY
    # ========================================
    output.append("=" * 100)
    output.append("SUMMARY BY MODEL")
    output.append("=" * 100)
    output.append("")

    for model in sorted(by_model.keys()):
        stats = by_model[model]
        total = stats['total_scenarios']
        avg_consensus = sum(stats['rates']) / len(stats['rates']) if stats['rates'] else 0
        unanimous_pct = 100 * stats['unanimous_count'] / total if total > 0 else 0

        output.append(f"Model: {model}")
        output.append(f"  Total scenarios: {total}")
        output.append(f"  Average consensus rate: {avg_consensus:.3f} ({avg_consensus*100:.1f}%)")
        output.append(f"  Unanimous (5/5): {stats['unanimous_count']} ({unanimous_pct:.1f}%)")
        output.append("")
        output.append("  Agreement distribution:")
        output.append(format_distribution(stats['distribution'], total))
        output.append("")
        output.append("-" * 100)
        output.append("")

    # ========================================
    # BY GAME SUMMARY
    # ========================================
    output.append("")
    output.append("=" * 100)
    output.append("SUMMARY BY GAME")
    output.append("=" * 100)
    output.append("")

    for game_key in sorted(by_game.keys()):
        stats = by_game[game_key]
        total = stats['total_scenarios']
        avg_consensus = sum(stats['rates']) / len(stats['rates']) if stats['rates'] else 0
        unanimous_pct = 100 * stats['unanimous_count'] / total if total > 0 else 0

        output.append(f"Game: {game_key}")
        output.append(f"  Total scenarios: {total}")
        output.append(f"  Average consensus rate: {avg_consensus:.3f} ({avg_consensus*100:.1f}%)")
        output.append(f"  Unanimous (5/5): {stats['unanimous_count']} ({unanimous_pct:.1f}%)")
        output.append("")
        output.append("  Agreement distribution:")
        output.append(format_distribution(stats['distribution'], total))
        output.append("")
        output.append("-" * 100)
        output.append("")

    # ========================================
    # DETAILED BREAKDOWN
    # ========================================
    output.append("")
    output.append("=" * 100)
    output.append("DETAILED BREAKDOWN (Game × Model)")
    output.append("=" * 100)
    output.append("")

    for key in sorted(consensus_data.keys()):
        stats = consensus_data[key]
        total = stats['total_scenarios']
        avg_consensus = sum(stats['rates']) / len(stats['rates']) if stats['rates'] else 0
        unanimous_pct = 100 * stats['unanimous_count'] / total if total > 0 else 0

        output.append(f"{key}:")
        output.append(f"  Total scenarios: {total}")
        output.append(f"  Average consensus rate: {avg_consensus:.3f} ({avg_consensus*100:.1f}%)")
        output.append(f"  Unanimous (5/5): {stats['unanimous_count']} ({unanimous_pct:.1f}%)")
        output.append("")
        output.append("  Agreement distribution:")
        output.append(format_distribution(stats['distribution'], total))
        output.append("")

    output.append("=" * 100)
    output.append("END OF CONSENSUS ANALYSIS")
    output.append("=" * 100)

    return "\n".join(output)


if __name__ == "__main__":
    try:
        consensus_data, by_model, by_game = analyze_consensus_stats()

        report = generate_report(consensus_data, by_model, by_game)

        # Save to file
        output_path = Path(__file__).parent.parent / "outputs" / "CONSENSUS_RATES.txt"
        with open(output_path, 'w') as f:
            f.write(report)

        print(report)
        print()
        print(f"Report saved to: {output_path}")
    except (FileNotFoundError, KeyError) as e:
        sys.exit(
            "\nThis script analyses result files from the original study, and the ones it\n"
            f"expects were not found under outputs/ ({e!r}).\n"
            "Run the matching experiment first, or point the paths at the top of this\n"
            "file at your own results."
        )
