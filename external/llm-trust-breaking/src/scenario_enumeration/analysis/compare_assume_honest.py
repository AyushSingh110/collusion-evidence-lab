"""
Compare lying rates between original and assume_honest experiments.

This script compares the results from:
- Original 3-agent experiments (without assume_honest flag)
- New 3-agent experiments (with assume_honest flag)

It calculates the difference in lying rates to see if assuming honesty
changes LLM behavior.
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path

# Models and games to analyze
MODELS = [
    "claude-sonnet-4.5",
    "gemini-3-flash-preview",
    "qwen3-8b",
    "qwen3-32b",
    "deepseek-v3.2",
    "gpt-4o",
    "gpt-5.2"
]

GAMES = [
    "volunteer",
    "congestion",
    "publicgoods",
    "fishing",
    "twothirds",
    "auction"
]

AGENTS = 3


def load_results(game: str, model: str, assume_honest: bool) -> Dict[str, Any]:
    """Load experiment results from JSON file."""
    suffix = "_assume_honest" if assume_honest else ""
    filename = f"{model}_r1{suffix}.json"
    filepath = f"outputs/experiments/{game}/{AGENTS}agents/{filename}"

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as f:
        return json.load(f)


def extract_lying_rate(results: Dict[str, Any]) -> float:
    """Extract empirical lying rate from results."""
    if results is None:
        return None
    return results['analysis']['summary']['empirical_lying_rate']


def calculate_differences():
    """Calculate lying rate differences for all model-game combinations."""

    print("="*100)
    print("COMPARING LYING RATES: Original vs Assume Honest")
    print("="*100)
    print()

    # Store all results for summary
    all_differences = []

    # Per-game analysis
    for game in GAMES:
        print(f"\n{'='*100}")
        print(f"GAME: {game.upper()}")
        print(f"{'='*100}")
        print(f"{'Model':<30} {'Original %':<15} {'Assume Honest %':<20} {'Difference':<15}")
        print("-"*100)

        game_differences = []

        for model in MODELS:
            # Load both versions
            original = load_results(game, model, assume_honest=False)
            assume_honest = load_results(game, model, assume_honest=True)

            # Extract lying rates
            original_rate = extract_lying_rate(original)
            assume_honest_rate = extract_lying_rate(assume_honest)

            if original_rate is not None and assume_honest_rate is not None:
                difference = assume_honest_rate - original_rate
                all_differences.append(difference)
                game_differences.append(difference)

                # Print comparison
                print(f"{model:<30} {original_rate*100:>13.2f}% {assume_honest_rate*100:>18.2f}% {difference*100:>14.2f}%")
            elif original_rate is None and assume_honest_rate is None:
                print(f"{model:<30} {'MISSING':>13} {'MISSING':>18} {'N/A':>14}")
            elif original_rate is None:
                print(f"{model:<30} {'MISSING':>13} {assume_honest_rate*100:>18.2f}% {'N/A':>14}")
            else:
                print(f"{model:<30} {original_rate*100:>13.2f}% {'MISSING':>18} {'N/A':>14}")

        # Game-level summary
        if game_differences:
            avg_diff = sum(game_differences) / len(game_differences)
            print("-"*100)
            print(f"{'Average difference for ' + game:<30} {avg_diff*100:>14.2f}%")

    # Overall summary
    print(f"\n\n{'='*100}")
    print("OVERALL SUMMARY")
    print(f"{'='*100}")

    if all_differences:
        avg_diff = sum(all_differences) / len(all_differences)
        min_diff = min(all_differences)
        max_diff = max(all_differences)

        print(f"Total comparisons: {len(all_differences)}")
        print(f"Average lying rate change: {avg_diff*100:+.2f}%")
        print(f"Min change: {min_diff*100:+.2f}%")
        print(f"Max change: {max_diff*100:+.2f}%")
        print()

        # Count how many increased vs decreased
        increased = sum(1 for d in all_differences if d > 0)
        decreased = sum(1 for d in all_differences if d < 0)
        unchanged = sum(1 for d in all_differences if abs(d) < 0.001)

        print(f"Lying rate increased (assume_honest > original): {increased}/{len(all_differences)}")
        print(f"Lying rate decreased (assume_honest < original): {decreased}/{len(all_differences)}")
        print(f"Lying rate unchanged: {unchanged}/{len(all_differences)}")

        print()
        print("Interpretation:")
        if avg_diff > 0.01:
            print("→ Assuming honesty INCREASES lying rate (agents exploit the assumption)")
        elif avg_diff < -0.01:
            print("→ Assuming honesty DECREASES lying rate (agents reciprocate trust)")
        else:
            print("→ Assuming honesty has MINIMAL effect on lying rate")
    else:
        print("No valid comparisons found. Run experiments first.")

    print(f"{'='*100}\n")


def create_latex_table():
    """Create a LaTeX table comparing the results."""

    print("\n" + "="*100)
    print("LATEX TABLE (for paper)")
    print("="*100)
    print()

    # LaTeX table header
    latex = "\\begin{table}[h]\n"
    latex += "\\centering\n"
    latex += "\\caption{Lying Rate Comparison: Original vs Assume Honest (3 agents)}\n"
    latex += "\\begin{tabular}{l" + "c"*len(GAMES) + "c}\n"
    latex += "\\hline\n"
    latex += "Model & " + " & ".join([g.capitalize() for g in GAMES]) + " & Avg \\\\\n"
    latex += "\\hline\n"

    # Collect data for each model
    for model in MODELS:
        model_short = model.split('-')[0]  # Shorten model name
        row = [model_short]
        model_diffs = []

        for game in GAMES:
            original = load_results(game, model, assume_honest=False)
            assume_honest = load_results(game, model, assume_honest=True)

            original_rate = extract_lying_rate(original)
            assume_honest_rate = extract_lying_rate(assume_honest)

            if original_rate is not None and assume_honest_rate is not None:
                diff = assume_honest_rate - original_rate
                model_diffs.append(diff)
                row.append(f"{diff*100:+.1f}\\%")
            else:
                row.append("--")

        # Add average
        if model_diffs:
            avg = sum(model_diffs) / len(model_diffs)
            row.append(f"{avg*100:+.1f}\\%")
        else:
            row.append("--")

        latex += " & ".join(row) + " \\\\\n"

    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\label{tab:assume_honest_comparison}\n"
    latex += "\\end{table}\n"

    print(latex)
    print()


if __name__ == "__main__":
    calculate_differences()
    create_latex_table()
