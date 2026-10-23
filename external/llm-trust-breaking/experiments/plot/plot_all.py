"""
Generate plots for all experiment files in outputs/experiments/.

Creates:
  1. Judge label distribution plots (per-trial, across rounds) via plot_judge.py
  2. Trust score evolution plots (per-trial, across rounds) via plot_trust.py
  3. Summary comparison plots (aggregate statistics across games/models)

Usage:
    python experiments/plot/plot_all.py
    python experiments/plot/plot_all.py --skip-individual  # only create summary plots
"""

import argparse
import json
import os
import sys
import glob
from pathlib import Path
import subprocess

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from collections import defaultdict


def find_experiment_files(base_dir="outputs/experiments"):
    """Find all endogenous experiment JSON files."""
    pattern = os.path.join(base_dir, "**", "*_endogenous.json")
    return sorted(glob.glob(pattern, recursive=True))


def load_data(path):
    """Load experiment JSON data."""
    with open(path) as f:
        return json.load(f)


def extract_summary_stats(data):
    """Extract aggregate deception statistics from an experiment."""
    meta = data.get("metadata", {})
    rounds = data.get("rounds", [])

    if not rounds:
        return None

    # Aggregate across all trials and rounds
    typology_counts = defaultdict(int)
    judge_counts = defaultdict(int)
    total_agents = 0
    promise_deception_count = 0
    commitment_breaking_count = 0

    for rd in rounds:
        for trial in rd["trials"]:
            for agent_name, agent_data in trial["agents"].items():
                total_agents += 1

                # Typology
                typology = agent_data.get("typology", "unknown")
                typology_counts[typology] += 1

                # Boolean measures
                if agent_data.get("promise_deception") is True:
                    promise_deception_count += 1
                if agent_data.get("commitment_breaking") is True:
                    commitment_breaking_count += 1

                # Judge labels
                judge = agent_data.get("judge", {})
                if judge.get("_parse_ok", False):
                    label = judge.get("primary_label", "Inconsistency / Error")
                    judge_counts[label] += 1

    if total_agents == 0:
        return None

    return {
        "game_type": meta.get("game_type", "unknown"),
        "model": meta.get("model", "unknown"),
        "n_trials": meta.get("n_trials", 0),
        "n_rounds": meta.get("n_rounds", 1),
        "total_agents": total_agents,
        "promise_deception_rate": promise_deception_count / total_agents,
        "commitment_breaking_rate": commitment_breaking_count / total_agents,
        "typology_rates": {k: v / total_agents for k, v in typology_counts.items()},
        "judge_rates": {k: v / total_agents for k, v in judge_counts.items()},
    }


def plot_deception_summary(all_stats, output_dir):
    """Create summary plots comparing deception rates across games and models."""
    os.makedirs(output_dir, exist_ok=True)

    # Group by game
    by_game = defaultdict(list)
    for stats in all_stats:
        by_game[stats["game_type"]].append(stats)

    games = sorted(by_game.keys())

    # --- Plot 1: Promise Deception Rate ---
    fig, ax = plt.subplots(figsize=(12, 6))

    x_pos = np.arange(len(games))
    width = 0.25

    # Get unique models
    all_models = sorted(set(s["model"] for s in all_stats))
    model_colors = {
        "openai/gpt-4o-mini": "#1f77b4",
        "openai/gpt-5-mini": "#ff7f0e",
        "anthropic/claude-sonnet-4.6": "#2ca02c",
    }

    for i, model in enumerate(all_models):
        rates = []
        for game in games:
            game_stats = [s for s in by_game[game] if s["model"] == model]
            if game_stats:
                rates.append(game_stats[0]["promise_deception_rate"] * 100)
            else:
                rates.append(0)

        offset = (i - len(all_models) / 2 + 0.5) * width
        ax.bar(
            x_pos + offset, rates, width,
            label=model.replace("openai/", "").replace("anthropic/", ""),
            color=model_colors.get(model, f"C{i}"),
            alpha=0.8,
        )

    ax.set_xlabel("Game", fontsize=11, fontweight="bold")
    ax.set_ylabel("Promise Deception Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Promise Deception Rate by Game and Model", fontsize=13, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([g.capitalize() for g in games], fontsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "promise_deception_by_game.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_dir}/promise_deception_by_game.png")

    # --- Plot 2: Commitment Breaking Rate ---
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, model in enumerate(all_models):
        rates = []
        for game in games:
            game_stats = [s for s in by_game[game] if s["model"] == model]
            if game_stats:
                rates.append(game_stats[0]["commitment_breaking_rate"] * 100)
            else:
                rates.append(0)

        offset = (i - len(all_models) / 2 + 0.5) * width
        ax.bar(
            x_pos + offset, rates, width,
            label=model.replace("openai/", "").replace("anthropic/", ""),
            color=model_colors.get(model, f"C{i}"),
            alpha=0.8,
        )

    ax.set_xlabel("Game", fontsize=11, fontweight="bold")
    ax.set_ylabel("Commitment Breaking Rate (%)", fontsize=11, fontweight="bold")
    ax.set_title("Commitment Breaking Rate by Game and Model", fontsize=13, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([g.capitalize() for g in games], fontsize=10)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "commitment_breaking_by_game.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_dir}/commitment_breaking_by_game.png")

    # --- Plot 3: Typology Distribution (stacked bar) ---
    typology_order = [
        "fully_honest",
        "intended_deceptive_complied",
        "impulsive_deviation",
        "premeditated_deception",
        "unknown",
    ]
    typology_colors = {
        "fully_honest": "#2ca02c",
        "intended_deceptive_complied": "#1f77b4",
        "impulsive_deviation": "#ff7f0e",
        "premeditated_deception": "#d62728",
        "unknown": "#7f7f7f",
    }
    typology_labels = {
        "fully_honest": "Fully Honest",
        "intended_deceptive_complied": "Intended Deceptive (Complied)",
        "impulsive_deviation": "Impulsive Deviation",
        "premeditated_deception": "Premeditated Deception",
        "unknown": "Unknown/Error",
    }

    fig, ax = plt.subplots(figsize=(14, 7))

    n_groups = len(games) * len(all_models)
    x_pos = np.arange(n_groups)

    # Build data matrix: rows = typologies, cols = (game, model) pairs
    data_matrix = {typ: [] for typ in typology_order}
    x_labels = []

    for game in games:
        for model in all_models:
            game_stats = [s for s in by_game[game] if s["model"] == model]
            if game_stats:
                rates = game_stats[0]["typology_rates"]
                for typ in typology_order:
                    data_matrix[typ].append(rates.get(typ, 0) * 100)
            else:
                for typ in typology_order:
                    data_matrix[typ].append(0)

            short_model = model.replace("openai/", "").replace("anthropic/", "").replace("gpt-", "").replace("claude-", "")
            x_labels.append(f"{game.capitalize()}\n{short_model}")

    # Stacked bars
    bottom = np.zeros(n_groups)
    for typ in typology_order:
        ax.bar(
            x_pos, data_matrix[typ], width=0.8,
            bottom=bottom,
            label=typology_labels[typ],
            color=typology_colors[typ],
            alpha=0.85,
        )
        bottom += np.array(data_matrix[typ])

    ax.set_ylabel("% of Agents", fontsize=11, fontweight="bold")
    ax.set_title("Deception Typology Distribution by Game and Model", fontsize=13, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8, rotation=0)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "typology_distribution.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_dir}/typology_distribution.png")

    # --- Plot 4: Judge Label Distribution (stacked bar) ---
    judge_order = [
        "Honest Consistency",
        "Justified Update",
        "Opportunistic Betrayal",
        "Premeditated Deception",
        "Inconsistency / Error",
    ]
    judge_colors = {
        "Honest Consistency": "#2ca02c",
        "Justified Update": "#1f77b4",
        "Opportunistic Betrayal": "#ff7f0e",
        "Premeditated Deception": "#d62728",
        "Inconsistency / Error": "#7f7f7f",
    }

    fig, ax = plt.subplots(figsize=(14, 7))

    data_matrix = {lbl: [] for lbl in judge_order}

    for game in games:
        for model in all_models:
            game_stats = [s for s in by_game[game] if s["model"] == model]
            if game_stats:
                rates = game_stats[0]["judge_rates"]
                for lbl in judge_order:
                    data_matrix[lbl].append(rates.get(lbl, 0) * 100)
            else:
                for lbl in judge_order:
                    data_matrix[lbl].append(0)

    bottom = np.zeros(n_groups)
    for lbl in judge_order:
        ax.bar(
            x_pos, data_matrix[lbl], width=0.8,
            bottom=bottom,
            label=lbl,
            color=judge_colors[lbl],
            alpha=0.85,
        )
        bottom += np.array(data_matrix[lbl])

    ax.set_ylabel("% of Agents", fontsize=11, fontweight="bold")
    ax.set_title("LLM-Judge Label Distribution by Game and Model", fontsize=13, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8, rotation=0)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "judge_distribution.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_dir}/judge_distribution.png")


def main():
    parser = argparse.ArgumentParser(description="Generate all plots for endogenous experiments.")
    parser.add_argument(
        "--skip-individual", action="store_true",
        help="Skip individual trial plots (judge/trust), only create summary plots."
    )
    parser.add_argument(
        "--base-dir", default="outputs/experiments",
        help="Base directory containing experiment outputs (default: outputs/experiments)."
    )
    args = parser.parse_args()

    files = find_experiment_files(args.base_dir)

    if not files:
        print(f"No experiment files found in {args.base_dir}")
        sys.exit(1)

    print(f"Found {len(files)} experiment file(s):\n")
    for f in files:
        print(f"  {f}")
    print()

    # Generate individual plots
    if not args.skip_individual:
        print("=" * 72)
        print("GENERATING INDIVIDUAL TRIAL PLOTS")
        print("=" * 72)

        for exp_file in files:
            print(f"\n--- {os.path.basename(exp_file)} ---")

            # Judge plots
            print("  Generating judge label plots...")
            subprocess.run([
                sys.executable, str(Path(__file__).parent / "plot_judge.py"), exp_file
            ], check=True)

            # Trust plots (only for multi-round experiments)
            data = load_data(exp_file)
            n_rounds = data.get("metadata", {}).get("n_rounds", 1)
            if n_rounds > 1:
                print("  Generating trust score plots...")
                subprocess.run([
                    sys.executable, str(Path(__file__).parent / "plot_trust.py"), exp_file
                ], check=True)
            else:
                print("  Skipping trust plots (single-round experiment)")

    # Generate summary plots
    print("\n" + "=" * 72)
    print("GENERATING SUMMARY COMPARISON PLOTS")
    print("=" * 72 + "\n")

    all_stats = []
    for exp_file in files:
        data = load_data(exp_file)
        stats = extract_summary_stats(data)
        if stats:
            all_stats.append(stats)

    if all_stats:
        output_dir = "outputs/plots/summary"
        plot_deception_summary(all_stats, output_dir)
        print(f"\nSummary plots saved to: {output_dir}/")
    else:
        print("No valid data for summary plots.")

    print("\n" + "=" * 72)
    print("ALL PLOTS GENERATED SUCCESSFULLY")
    print("=" * 72)


if __name__ == "__main__":
    main()
