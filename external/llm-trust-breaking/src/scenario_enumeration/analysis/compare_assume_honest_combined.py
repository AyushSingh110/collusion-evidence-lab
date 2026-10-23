"""
Combined comparison of lying rates for 3 and 4 agents.
Shows side-by-side comparison of the assume_honest effect.
"""

import json
import os
from typing import Dict, Any, List

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


def load_results(game: str, model: str, agents: int, assume_honest: bool) -> Dict[str, Any]:
    """Load experiment results from JSON file."""
    suffix = "_assume_honest" if assume_honest else ""
    filename = f"{model}_r1{suffix}.json"
    filepath = f"outputs/experiments/{game}/{agents}agents/{filename}"

    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as f:
        return json.load(f)


def extract_lying_rate(results: Dict[str, Any]) -> float:
    """Extract empirical lying rate from results."""
    if results is None:
        return None
    return results['analysis']['summary']['empirical_lying_rate']


def calculate_combined_summary():
    """Calculate summary across both agent counts."""

    print("="*120)
    print("ASSUME HONEST EFFECT: COMBINED SUMMARY (3 vs 4 AGENTS)")
    print("="*120)
    print()

    # Calculate for each agent count
    for agents in [3, 4]:
        print(f"\n{'='*120}")
        print(f"{agents} AGENTS - OVERALL EFFECT BY MODEL")
        print(f"{'='*120}")
        print(f"{'Model':<30} {'Avg Change %':<15} {'Increased':<12} {'Decreased':<12} {'Unchanged':<12}")
        print("-"*120)

        for model in MODELS:
            model_diffs = []

            for game in GAMES:
                original = load_results(game, model, agents, assume_honest=False)
                assume_honest = load_results(game, model, agents, assume_honest=True)

                original_rate = extract_lying_rate(original)
                assume_honest_rate = extract_lying_rate(assume_honest)

                if original_rate is not None and assume_honest_rate is not None:
                    diff = assume_honest_rate - original_rate
                    model_diffs.append(diff)

            if model_diffs:
                avg = sum(model_diffs) / len(model_diffs)
                increased = sum(1 for d in model_diffs if d > 0.001)
                decreased = sum(1 for d in model_diffs if d < -0.001)
                unchanged = sum(1 for d in model_diffs if abs(d) <= 0.001)

                print(f"{model:<30} {avg*100:>13.2f}% {increased:>10}/6 {decreased:>10}/6 {unchanged:>10}/6")

    # Overall comparison
    print(f"\n\n{'='*120}")
    print("OVERALL EFFECT ACROSS ALL GAMES AND MODELS")
    print(f"{'='*120}")
    print(f"{'Agent Count':<15} {'Avg Change':<15} {'Increased':<15} {'Decreased':<15} {'Unchanged':<15}")
    print("-"*120)

    for agents in [3, 4]:
        all_diffs = []

        for model in MODELS:
            for game in GAMES:
                original = load_results(game, model, agents, assume_honest=False)
                assume_honest = load_results(game, model, agents, assume_honest=True)

                original_rate = extract_lying_rate(original)
                assume_honest_rate = extract_lying_rate(assume_honest)

                if original_rate is not None and assume_honest_rate is not None:
                    diff = assume_honest_rate - original_rate
                    all_diffs.append(diff)

        if all_diffs:
            avg = sum(all_diffs) / len(all_diffs)
            increased = sum(1 for d in all_diffs if d > 0.001)
            decreased = sum(1 for d in all_diffs if d < -0.001)
            unchanged = sum(1 for d in all_diffs if abs(d) <= 0.001)

            print(f"{agents} agents {avg*100:>13.2f}% {increased:>13}/{len(all_diffs)} {decreased:>13}/{len(all_diffs)} {unchanged:>13}/{len(all_diffs)}")

    print(f"{'='*120}\n")


def create_combined_latex_table():
    """Create a combined LaTeX table for both agent counts."""

    print("\n" + "="*120)
    print("COMBINED LATEX TABLE")
    print("="*120)
    print()

    latex = "\\begin{table}[h]\n"
    latex += "\\centering\n"
    latex += "\\caption{Effect of Assuming Honesty on Lying Rates (\\% change)}\n"
    latex += "\\begin{tabular}{ll" + "c"*len(GAMES) + "c}\n"
    latex += "\\hline\n"
    latex += "Agents & Model & " + " & ".join([g.capitalize() for g in GAMES]) + " & Avg \\\\\n"
    latex += "\\hline\n"

    for agents in [3, 4]:
        for idx, model in enumerate(MODELS):
            model_short = model.replace('-sonnet-4.5', '').replace('-3-flash-preview', '').replace('3-', '')
            model_short = model_short.split('-')[0]  # First part only

            row = []
            if idx == 0:
                row.append(f"\\multirow{{{len(MODELS)}}}{{*}}{{{agents}}}")
            else:
                row.append("")

            row.append(model_short)
            model_diffs = []

            for game in GAMES:
                original = load_results(game, model, agents, assume_honest=False)
                assume_honest = load_results(game, model, agents, assume_honest=True)

                original_rate = extract_lying_rate(original)
                assume_honest_rate = extract_lying_rate(assume_honest)

                if original_rate is not None and assume_honest_rate is not None:
                    diff = assume_honest_rate - original_rate
                    model_diffs.append(diff)
                    row.append(f"{diff*100:+.1f}")
                else:
                    row.append("--")

            # Add average
            if model_diffs:
                avg = sum(model_diffs) / len(model_diffs)
                row.append(f"\\textbf{{{avg*100:+.1f}}}")
            else:
                row.append("--")

            latex += " & ".join(row) + " \\\\\n"

        if agents == 3:
            latex += "\\hline\n"

    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\label{tab:assume_honest_combined}\n"
    latex += "\\end{table}\n"

    print(latex)
    print()


if __name__ == "__main__":
    calculate_combined_summary()
    create_combined_latex_table()
