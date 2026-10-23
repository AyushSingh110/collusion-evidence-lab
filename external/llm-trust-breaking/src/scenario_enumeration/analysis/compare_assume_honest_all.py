"""
Comprehensive comparison across 3, 4, and 5 agents.
"""

import json
import os
import glob

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

AGENT_COUNTS = [3, 4, 5]


def discover_models(agents=None):
    """
    Find the models that actually have results on disk.

    With no agent count, look across every agent count.

    The hardcoded MODELS list above only matches the original research runs. Anyone
    running this project with a different model would get an empty comparison, so the
    filesystem is the source of truth and MODELS is the fallback ordering.
    """
    found = set()
    pattern = f"outputs/experiments/*/{agents}agents/*_r1.json" if agents is not None \
        else "outputs/experiments/*/*agents/*_r1.json"
    for path in glob.glob(pattern):
        name = os.path.basename(path)[: -len("_r1.json")]
        found.add(name)
    if not found:
        return MODELS
    ordered = [m for m in MODELS if m in found]
    return ordered + sorted(found - set(ordered))


def load_results(game, model, agents, assume_honest):
    suffix = "_assume_honest" if assume_honest else ""
    filepath = f"outputs/experiments/{game}/{agents}agents/{model}_r1{suffix}.json"
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_lying_rate(results):
    if results is None:
        return None
    return results['analysis']['summary']['empirical_lying_rate']


def main():
    print("="*120)
    print("ASSUME HONEST EFFECT: COMPREHENSIVE SUMMARY (3, 4, 5 AGENTS)")
    print("="*120)
    print()

    # Overall statistics for each agent count
    print(f"\n{'='*120}")
    print("OVERALL EFFECT BY AGENT COUNT")
    print(f"{'='*120}")
    print(f"{'Agents':<10} {'Avg Change':<15} {'Increased':<15} {'Decreased':<15} {'Unchanged':<15} {'Total':<10}")
    print("-"*120)

    for agents in AGENT_COUNTS:
        all_diffs = []

        for model in discover_models(agents):
            for game in GAMES:
                original = load_results(game, model, agents, False)
                assume_honest = load_results(game, model, agents, True)

                orig_rate = extract_lying_rate(original)
                assume_rate = extract_lying_rate(assume_honest)

                if orig_rate is not None and assume_rate is not None:
                    all_diffs.append(assume_rate - orig_rate)

        if all_diffs:
            avg = sum(all_diffs) / len(all_diffs)
            increased = sum(1 for d in all_diffs if d > 0.001)
            decreased = sum(1 for d in all_diffs if d < -0.001)
            unchanged = sum(1 for d in all_diffs if abs(d) <= 0.001)

            print(f"{agents:<10} {avg*100:>13.2f}% {increased:>13}/{len(all_diffs)} {decreased:>13}/{len(all_diffs)} {unchanged:>13}/{len(all_diffs)} {len(all_diffs):>8}")

    # Per-model summary across all agent counts
    print(f"\n\n{'='*120}")
    print("PER-MODEL SUMMARY (AVERAGED ACROSS ALL GAMES AND AGENT COUNTS)")
    print(f"{'='*120}")
    print(f"{'Model':<30} {'3 Agents':<15} {'4 Agents':<15} {'5 Agents':<15} {'Overall Avg':<15}")
    print("-"*120)

    for model in discover_models():
        model_avgs = []

        for agents in AGENT_COUNTS:
            diffs = []
            for game in GAMES:
                original = load_results(game, model, agents, False)
                assume_honest = load_results(game, model, agents, True)

                orig_rate = extract_lying_rate(original)
                assume_rate = extract_lying_rate(assume_honest)

                if orig_rate is not None and assume_rate is not None:
                    diffs.append(assume_rate - orig_rate)

            if diffs:
                avg = sum(diffs) / len(diffs)
                model_avgs.append(avg)
            else:
                model_avgs.append(None)

        # Print row
        row = [model]
        for avg in model_avgs:
            if avg is not None:
                row.append(f"{avg*100:>13.2f}%")
            else:
                row.append("MISSING".rjust(15))

        # Overall average
        valid_avgs = [a for a in model_avgs if a is not None]
        if valid_avgs:
            overall = sum(valid_avgs) / len(valid_avgs)
            row.append(f"{overall*100:>13.2f}%")
        else:
            row.append("MISSING".rjust(15))

        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}")

    # Per-game summary across all agent counts
    print(f"\n\n{'='*120}")
    print("PER-GAME SUMMARY (AVERAGED ACROSS ALL MODELS AND AGENT COUNTS)")
    print(f"{'='*120}")
    print(f"{'Game':<15} {'3 Agents':<15} {'4 Agents':<15} {'5 Agents':<15} {'Overall Avg':<15}")
    print("-"*120)

    for game in GAMES:
        game_avgs = []

        for agents in AGENT_COUNTS:
            diffs = []
            for model in discover_models(agents):
                original = load_results(game, model, agents, False)
                assume_honest = load_results(game, model, agents, True)

                orig_rate = extract_lying_rate(original)
                assume_rate = extract_lying_rate(assume_honest)

                if orig_rate is not None and assume_rate is not None:
                    diffs.append(assume_rate - orig_rate)

            if diffs:
                avg = sum(diffs) / len(diffs)
                game_avgs.append(avg)
            else:
                game_avgs.append(None)

        # Print row
        row = [game]
        for avg in game_avgs:
            if avg is not None:
                row.append(f"{avg*100:>13.2f}%")
            else:
                row.append("MISSING".rjust(15))

        # Overall average
        valid_avgs = [a for a in game_avgs if a is not None]
        if valid_avgs:
            overall = sum(valid_avgs) / len(valid_avgs)
            row.append(f"{overall*100:>13.2f}%")
        else:
            row.append("MISSING".rjust(15))

        print(f"{row[0]:<15} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}")

    # Grand total
    print(f"\n\n{'='*120}")
    print("GRAND SUMMARY")
    print(f"{'='*120}")

    all_diffs_total = []
    for agents in AGENT_COUNTS:
        for model in discover_models(agents):
            for game in GAMES:
                original = load_results(game, model, agents, False)
                assume_honest = load_results(game, model, agents, True)

                orig_rate = extract_lying_rate(original)
                assume_rate = extract_lying_rate(assume_honest)

                if orig_rate is not None and assume_rate is not None:
                    all_diffs_total.append(assume_rate - orig_rate)

    if all_diffs_total:
        avg_total = sum(all_diffs_total) / len(all_diffs_total)
        increased_total = sum(1 for d in all_diffs_total if d > 0.001)
        decreased_total = sum(1 for d in all_diffs_total if d < -0.001)
        unchanged_total = sum(1 for d in all_diffs_total if abs(d) <= 0.001)

        print(f"Total comparisons: {len(all_diffs_total)} (7 models × 6 games × 3 agent counts)")
        print(f"Average lying rate change: {avg_total*100:+.2f}%")
        print(f"Min change: {min(all_diffs_total)*100:+.2f}%")
        print(f"Max change: {max(all_diffs_total)*100:+.2f}%")
        print()
        print(f"Lying increased: {increased_total}/{len(all_diffs_total)} ({increased_total/len(all_diffs_total)*100:.1f}%)")
        print(f"Lying decreased: {decreased_total}/{len(all_diffs_total)} ({decreased_total/len(all_diffs_total)*100:.1f}%)")
        print(f"No change: {unchanged_total}/{len(all_diffs_total)} ({unchanged_total/len(all_diffs_total)*100:.1f}%)")
        print()
        print("INTERPRETATION:")
        if avg_total > 0.01:
            print("→ Assuming honesty INCREASES lying rate (agents exploit the assumption)")
        elif avg_total < -0.01:
            print("→ Assuming honesty DECREASES lying rate (agents reciprocate trust)")
        else:
            print("→ Assuming honesty has MINIMAL effect on lying rate")

    print(f"{'='*120}\n")


if __name__ == "__main__":
    main()
