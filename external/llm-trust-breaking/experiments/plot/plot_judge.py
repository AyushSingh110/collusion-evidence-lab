"""
Plot LLM-judge label distribution across rounds for endogenous experiments.

Mirrors plot_trust.py: produces one PNG per trial.
Each plot shows a line per judge label, x-axis = round number,
y-axis = % of agents in that trial classified with that label.

Usage:
    python experiments/plot_judge.py <path/to/endogenous.json>
    python experiments/plot_judge.py <path/to/endogenous.json> --output-dir outputs/plots/judge
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


JUDGE_LABELS = [
    "Honest Consistency",
    "Justified Update",
    "Opportunistic Betrayal",
    "Premeditated Deception",
    "Inconsistency / Error",
]

LABEL_COLOURS = {
    "Honest Consistency":     "#2ca02c",
    "Justified Update":       "#1f77b4",
    "Opportunistic Betrayal": "#ff7f0e",
    "Premeditated Deception": "#d62728",
    "Inconsistency / Error":  "#7f7f7f",
}


def extract_judge_rates(rounds: list, trial_idx: int) -> dict:
    """
    Returns {round_id: {label: fraction_of_agents (0.0–1.0)}}
    for one trial across all rounds.
    Only counts agents where judge._parse_ok is True.
    """
    result = {}
    for rd in rounds:
        round_id = rd["round_id"]
        trial = next((t for t in rd["trials"] if t["trial_id"] == trial_idx), None)
        if trial is None:
            continue

        counts: dict = defaultdict(int)
        total = 0
        for agent_data in trial["agents"].values():
            j = agent_data.get("judge", {})
            if j.get("_parse_ok", False):
                counts[j.get("primary_label", "Inconsistency / Error")] += 1
                total += 1

        if total > 0:
            result[round_id] = {lbl: counts.get(lbl, 0) / total for lbl in JUDGE_LABELS}

    return result


def plot_trial(
    trial_idx: int,
    rates_by_round: dict,
    game_type: str,
    model: str,
    output_dir: str,
):
    if not rates_by_round:
        print(f"  Trial {trial_idx + 1}: no valid judge labels — skipping.")
        return

    round_ids = sorted(rates_by_round.keys())
    x_labels  = [f"Round {r + 1}" for r in round_ids]
    xs        = list(range(len(round_ids)))

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(
        f"{game_type} · {model} · Trial {trial_idx + 1} — judge label distribution",
        fontsize=12, fontweight="bold",
    )

    for label in JUDGE_LABELS:
        ys = [rates_by_round[r].get(label, 0.0) * 100 for r in round_ids]
        ax.plot(
            xs, ys,
            marker="o", linewidth=2, markersize=6,
            color=LABEL_COLOURS[label], label=label,
        )

    ax.set_xlabel("Round", fontsize=10)
    ax.set_ylabel("% of agents", fontsize=10)
    ax.set_ylim(-5, 105)
    ax.set_xticks(xs)
    ax.set_xticklabels(x_labels, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.8)

    plt.tight_layout()
    fname = os.path.join(output_dir, f"trial_{trial_idx + 1:02d}.png")
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {fname}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot LLM-judge label distribution per trial across rounds."
    )
    parser.add_argument("json_file", help="Path to endogenous experiment JSON output.")
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to save PNGs (default: outputs/plots/judge/<stem>/).",
    )
    args = parser.parse_args()

    with open(args.json_file) as f:
        data = json.load(f)

    meta   = data.get("metadata", {})
    rounds = data.get("rounds", [])

    if not rounds:
        print("No rounds found in the file.")
        sys.exit(1)

    n_rounds  = meta.get("n_rounds", len(rounds))
    n_trials  = meta.get("n_trials", max(len(r["trials"]) for r in rounds))
    game_type = meta.get("game_type", "unknown")
    model     = meta.get("model", "unknown")
    trial_ids = sorted({t["trial_id"] for r in rounds for t in r["trials"]})

    if args.output_dir:
        output_dir = args.output_dir
    else:
        safe_model = model.replace("/", "_").replace(":", "_")
        output_dir = os.path.join("outputs", "plots", "judge", game_type, safe_model)

    os.makedirs(output_dir, exist_ok=True)
    print(f"Game: {game_type}  |  Model: {model}  |  Trials: {n_trials}  |  Rounds: {n_rounds}")
    print(f"Output dir: {output_dir}\n")

    for trial_idx in trial_ids:
        rates_by_round = extract_judge_rates(rounds, trial_idx)
        plot_trial(
            trial_idx=trial_idx,
            rates_by_round=rates_by_round,
            game_type=game_type,
            model=model,
            output_dir=output_dir,
        )

    print(f"\nDone — {len(trial_ids)} plot(s) written to {output_dir}/")


if __name__ == "__main__":
    main()
