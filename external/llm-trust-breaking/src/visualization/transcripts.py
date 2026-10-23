"""
Generate human-readable Markdown transcripts from experiment JSON data.

Creates one .md file per trial showing the complete narrative across all rounds:
- Stage 1: Private planning (intended actions + reasoning)
- Stage 2: Public announcements (stated actions + messages)
- Stage 3: Final actions (choices + payoffs + outcomes)
- Trust updates: Agent beliefs after each round

Usage:
    python experiments/generate_transcripts.py <path/to/experiment.json>
    python experiments/generate_transcripts.py <path/to/experiment.json> --output-dir outputs/transcripts
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_data(path: str) -> dict:
    """Load experiment JSON data."""
    with open(path) as f:
        return json.load(f)


def format_action_comparison(intended, stated, actual):
    """Format the comparison of intended vs stated vs actual actions."""
    parts = []

    # Compare intended (Stage 1) vs stated (Stage 2)
    if intended != stated:
        parts.append(f"planned {intended} but announced {stated}")

    # Compare stated (Stage 2) vs actual (Stage 3)
    if stated != actual:
        if parts:
            parts.append(f"then chose {actual}")
        else:
            parts.append(f"announced {stated} but chose {actual}")
        symbol = "❌"
    else:
        if parts:
            parts.append(f"and kept promise by choosing {actual}")
        else:
            parts.append(f"kept promise")
        symbol = "✓"

    return symbol, " ".join(parts)


def generate_trial_transcript(trial_id: int, trial_data_across_rounds: list, metadata: dict) -> str:
    """
    Generate a Markdown transcript for a single trial across all rounds.

    Args:
        trial_id: The trial index
        trial_data_across_rounds: List of round dicts, each with trials data
        metadata: Experiment metadata

    Returns:
        Markdown string
    """
    game_type = metadata.get("game_type", "unknown")
    model = metadata.get("model", "unknown")
    n_rounds = metadata.get("n_rounds", len(trial_data_across_rounds))
    n_agents = metadata.get("n_agents", 0)

    # Get agent names from first round
    first_round = trial_data_across_rounds[0]
    first_trial = next((t for t in first_round["trials"] if t["trial_id"] == trial_id), None)
    if not first_trial:
        return ""

    agent_names = sorted(first_trial["agents"].keys())

    # Build markdown
    lines = []
    lines.append(f"# Trial {trial_id + 1} - {game_type.capitalize()}")
    lines.append(f"\n**Model:** {model}")
    lines.append(f"**Agents:** {', '.join(agent_names)}")
    lines.append(f"**Rounds:** {n_rounds}")
    lines.append("\n---\n")

    # Process each round
    for round_data in trial_data_across_rounds:
        round_idx = round_data["round_id"]
        trial = next((t for t in round_data["trials"] if t["trial_id"] == trial_id), None)

        if not trial:
            continue

        lines.append(f"## Round {round_idx + 1}\n")

        # Stage 1: Private Planning
        lines.append("### Stage 1: Private Planning (Hidden from Others)\n")
        for agent_name in agent_names:
            agent_data = trial["agents"][agent_name]
            stage1 = agent_data.get("stage1", {})

            intended = stage1.get("intended_action", "unknown")
            reasoning = stage1.get("reasoning", "No reasoning provided")

            lines.append(f"**Agent {agent_name}**")
            lines.append(f"- **Intended Action:** {intended}")
            lines.append(f"- **Reasoning:** \"{reasoning}\"")
            lines.append("")

        # Stage 2: Public Announcements
        lines.append("### Stage 2: Public Announcements\n")
        for agent_name in agent_names:
            agent_data = trial["agents"][agent_name]
            stage2 = agent_data.get("stage2", {})

            stated = stage2.get("stated_action", "unknown")
            message = stage2.get("message", "No message")

            lines.append(f"**Agent {agent_name}** announced **{stated}**")
            lines.append(f"> \"{message}\"")
            lines.append("")

        # Stage 3: Final Actions & Outcomes
        lines.append("### Stage 3: Final Actions & Outcomes\n")
        lines.append("**Actions:**")

        for agent_name in agent_names:
            agent_data = trial["agents"][agent_name]
            stage1 = agent_data.get("stage1", {})
            stage2 = agent_data.get("stage2", {})
            stage3 = agent_data.get("stage3", {})

            intended = stage1.get("intended_action", "unknown")
            stated = stage2.get("stated_action", "unknown")
            actual = stage3.get("choice", "unknown")

            symbol, comparison = format_action_comparison(intended, stated, actual)
            lines.append(f"- Agent {agent_name} {symbol} {comparison}")

        lines.append("\n**Payoffs:**")
        outcomes = trial.get("outcomes", {})
        payoffs = outcomes.get("payoffs", {})
        for agent_name in agent_names:
            payoff = payoffs.get(agent_name, 0.0)
            lines.append(f"- Agent {agent_name}: {payoff:.1f}")

        description = outcomes.get("description", "No description")
        lines.append(f"\n**Outcome:** {description}")
        lines.append("")

        # Trust Updates (if present)
        has_reflections = any(
            "reflection" in trial["agents"][a] and trial["agents"][a]["reflection"].get("_parse_ok")
            for a in agent_names
        )

        if has_reflections:
            lines.append("### Trust Updates\n")
            for agent_name in agent_names:
                agent_data = trial["agents"][agent_name]
                reflection = agent_data.get("reflection", {})

                if not reflection.get("_parse_ok"):
                    continue

                takeaways = reflection.get("takeaways", {})
                if not takeaways:
                    continue

                lines.append(f"**Agent {agent_name}:**")
                for target_agent in agent_names:
                    if target_agent == agent_name:
                        continue

                    takeaway = takeaways.get(target_agent)
                    if takeaway and isinstance(takeaway, dict):
                        score = takeaway.get("score", "?")
                        assessment = takeaway.get("assessment", "No assessment")
                        lines.append(f"- Agent {target_agent} (trust: {score}/5): \"{assessment}\"")

                lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate human-readable Markdown transcripts from experiment data."
    )
    parser.add_argument("json_file", help="Path to experiment JSON output")
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory for transcripts (default: outputs/transcripts/<game>/<model>/)"
    )
    args = parser.parse_args()

    # Load data
    data = load_data(args.json_file)
    metadata = data.get("metadata", {})
    rounds = data.get("rounds", [])

    if not rounds:
        print("No rounds found in the file.")
        sys.exit(1)

    game_type = metadata.get("game_type", "unknown")
    model = metadata.get("model", "unknown")
    n_trials = metadata.get("n_trials", 0)

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        safe_model = model.replace("/", "_").replace(":", "_")
        output_dir = os.path.join("outputs", "transcripts", game_type, safe_model)

    os.makedirs(output_dir, exist_ok=True)

    # Get all trial IDs
    trial_ids = sorted({t["trial_id"] for r in rounds for t in r["trials"]})

    print(f"Generating transcripts for {len(trial_ids)} trial(s)...")
    print(f"Output directory: {output_dir}\n")

    # Generate one file per trial
    for trial_id in trial_ids:
        markdown = generate_trial_transcript(trial_id, rounds, metadata)

        if not markdown:
            print(f"  Warning: No data for trial {trial_id}")
            continue

        filename = f"trial_{trial_id + 1:02d}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(markdown)

        print(f"  ✓ {filename}")

    print(f"\nDone — {len(trial_ids)} transcript(s) written to {output_dir}/")


if __name__ == "__main__":
    main()
