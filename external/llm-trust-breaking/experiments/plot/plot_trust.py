"""
Plot trust score evolution across rounds for endogenous multi-round experiments.

For each trial, produces a single image with two subplots:

  (a) Trust received — for each agent, the average score all OTHER agents
      assigned to them after each round.

  (b) Trust given — for each agent, the average score they assigned to all
      OTHER agents after each round.

X-axis: round after which reflection scores were recorded (rounds 1 … N-1).
One PNG per trial saved to --output-dir.

Usage:
    python experiments/plot_trust.py <path/to/endogenous.json>
    python experiments/plot_trust.py <path/to/endogenous.json> --output-dir outputs/plots/trust
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ── colour cycle consistent across subplots ──────────────────────────────────
COLOURS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


def load_data(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def extract_trust_scores(trial_data_across_rounds: list, trial_idx: int) -> dict:
    """
    Returns a nested dict:
        scores[round_id][giver][receiver] = int (1-5)

    Only rounds that have valid reflection data are included.
    """
    scores = {}
    for rd in trial_data_across_rounds:
        round_id = rd["round_id"]
        # Find this trial in the round
        trial = next(
            (t for t in rd["trials"] if t["trial_id"] == trial_idx), None
        )
        if trial is None:
            continue

        round_scores = {}
        for giver, agent_data in trial["agents"].items():
            refl = agent_data.get("reflection", {})
            if not refl.get("_parse_ok", False):
                continue
            takeaways = refl.get("takeaways", {})
            giver_scores = {}
            for receiver, val in takeaways.items():
                if isinstance(val, dict) and "score" in val:
                    giver_scores[receiver] = val["score"]
            if giver_scores:
                round_scores[giver] = giver_scores

        if round_scores:
            scores[round_id] = round_scores

    return scores


def compute_received(scores: dict, agent_names: list) -> dict:
    """avg score agent received from others, keyed by (agent, round_id)."""
    received = defaultdict(dict)
    for round_id, givers in scores.items():
        for receiver in agent_names:
            vals = [
                givers[giver][receiver]
                for giver in givers
                if receiver in givers[giver]
            ]
            if vals:
                received[receiver][round_id] = sum(vals) / len(vals)
    return received


def compute_given(scores: dict, agent_names: list) -> dict:
    """avg score agent gave to others, keyed by (agent, round_id)."""
    given = defaultdict(dict)
    for round_id, givers in scores.items():
        for giver in agent_names:
            if giver not in givers:
                continue
            vals = list(givers[giver].values())
            if vals:
                given[giver][round_id] = sum(vals) / len(vals)
    return given


def plot_trial(
    trial_idx: int,
    agent_names: list,
    scores: dict,
    game_type: str,
    model: str,
    n_rounds: int,
    output_dir: str,
):
    if not scores:
        print(f"  Trial {trial_idx}: no reflection data — skipping.")
        return

    received = compute_received(scores, agent_names)
    given    = compute_given(scores, agent_names)

    # x-axis: sorted round ids that have data
    round_ids = sorted(scores.keys())
    x_labels  = [f"After R{r + 1}" for r in round_ids]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    fig.suptitle(
        f"{game_type} · {model} · Trial {trial_idx + 1}",
        fontsize=13, fontweight="bold", y=1.01,
    )

    colour_map = {a: COLOURS[i % len(COLOURS)] for i, a in enumerate(agent_names)}

    def _plot_series(ax, data: dict, title: str, ylabel: str):
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Round (after reflection)", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_ylim(0.5, 5.5)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
        ax.set_xticks(range(len(round_ids)))
        ax.set_xticklabels(x_labels, fontsize=8)
        ax.axhline(3, color="grey", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.grid(axis="y", alpha=0.3)

        for agent in agent_names:
            ys = [data[agent].get(r) for r in round_ids]
            # Only plot if at least one point exists
            if all(y is None for y in ys):
                continue
            xs_plot = [i for i, y in enumerate(ys) if y is not None]
            ys_plot = [y for y in ys if y is not None]
            ax.plot(
                xs_plot, ys_plot,
                marker="o", linewidth=2, markersize=6,
                color=colour_map[agent], label=f"Agent {agent}",
            )

        ax.legend(fontsize=8, loc="upper left", framealpha=0.7)

    _plot_series(
        ax_a, received,
        title="(a) Trust received\navg score given TO each agent by all others",
        ylabel="Average trust score (1–5)",
    )
    _plot_series(
        ax_b, given,
        title="(b) Trust given\navg score each agent gives to all others",
        ylabel="",
    )

    plt.tight_layout()
    fname = os.path.join(output_dir, f"trial_{trial_idx + 1:02d}.png")
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {fname}")


def main():
    parser = argparse.ArgumentParser(description="Plot trust score evolution per trial.")
    parser.add_argument("json_file", help="Path to endogenous experiment JSON output.")
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory to save PNGs (default: outputs/plots/trust/<stem>/).",
    )
    args = parser.parse_args()

    data = load_data(args.json_file)
    meta   = data.get("metadata", {})
    rounds = data.get("rounds", [])

    if not rounds:
        print("No rounds found in the file.")
        sys.exit(1)

    n_rounds   = meta.get("n_rounds", len(rounds))
    n_trials   = meta.get("n_trials", max(len(r["trials"]) for r in rounds))
    game_type  = meta.get("game_type", "unknown")
    model      = meta.get("model", "unknown")

    # Infer agent names from the first trial of the first round
    first_trial = rounds[0]["trials"][0]
    agent_names = list(first_trial["agents"].keys())
    trial_ids   = sorted({t["trial_id"] for r in rounds for t in r["trials"]})

    if args.output_dir:
        output_dir = args.output_dir
    else:
        safe_model = model.replace("/", "_").replace(":", "_")
        output_dir = os.path.join("outputs", "plots", "trust", game_type, safe_model)

    os.makedirs(output_dir, exist_ok=True)
    print(f"Game: {game_type}  |  Model: {model}  |  Trials: {n_trials}  |  Rounds: {n_rounds}")
    print(f"Output dir: {output_dir}\n")

    for trial_idx in trial_ids:
        scores = extract_trust_scores(rounds, trial_idx)
        plot_trial(
            trial_idx=trial_idx,
            agent_names=agent_names,
            scores=scores,
            game_type=game_type,
            model=model,
            n_rounds=n_rounds,
            output_dir=output_dir,
        )

    print(f"\nDone — {len(trial_ids)} plot(s) written to {output_dir}/")


if __name__ == "__main__":
    main()
